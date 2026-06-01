"""Citation verification and management."""

import json
import math
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class VerificationLevel(Enum):
    """Citation verification levels."""

    UNVERIFIED = 0
    ARXIV_VERIFIED = 1
    DOI_VERIFIED = 2
    SEMANTIC_SCHOLAR_VERIFIED = 3
    LLM_RELEVANCE_CHECKED = 4
    FULLY_VERIFIED = 5


@dataclass
class VerificationCheck:
    """One evidence check performed while verifying a citation."""

    name: str
    source: str
    passed: bool
    detail: str


@dataclass
class VerificationResult:
    """Auditable result for a citation verification run."""

    citation: "Citation"
    passed: bool
    level: VerificationLevel
    checks: list[VerificationCheck]
    issues: list[str]
    warnings: list[str] = field(default_factory=list)

    @property
    def checks_by_name(self) -> dict[str, VerificationCheck]:
        """Return the first check for each logical check name."""
        by_name: dict[str, VerificationCheck] = {}
        for check in self.checks:
            by_name.setdefault(check.name, check)
        return by_name


@dataclass
class _MetadataLookupResult:
    """Metadata fetched from a live source or read from local cache."""

    paper: Optional[dict]
    cache_hit: bool = False


class _MetadataCache:
    """Tiny JSON cache for external metadata lookups."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def get(self, source: str, key: str) -> Optional[dict]:
        """Return cached metadata for source/key, or None if unavailable."""
        path = self._path(source, key)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        return data if isinstance(data, dict) else None

    def set(self, source: str, key: str, paper: Optional[dict]) -> None:
        """Persist a successful metadata lookup."""
        if not paper:
            return
        path = self._path(source, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(paper, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _path(self, source: str, key: str) -> Path:
        safe_source = _cache_path_part(source)
        safe_key = _cache_path_part(key)
        return self.root / safe_source / f"{safe_key}.json"


@dataclass
class Citation:
    """A verified citation."""

    title: str
    authors: list[str]
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    verification_level: VerificationLevel = VerificationLevel.UNVERIFIED
    relevance_score: Optional[float] = None
    verification_issues: list[str] = field(default_factory=list)

    def to_bibtex(self, key: str) -> str:
        """Convert citation to BibTeX format."""
        lines = [f"@article{{{key},"]
        lines.append(f"  title = {{{self.title}}},")

        if self.authors:
            authors_str = " and ".join(self.authors)
            lines.append(f"  author = {{{authors_str}}},")

        if self.year:
            lines.append(f"  year = {{{self.year}}},")

        if self.arxiv_id:
            lines.append(f"  eprint = {{{self.arxiv_id}}},")
            lines.append("  archiveprefix = {arXiv},")

        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")

        if self.url:
            lines.append(f"  url = {{{self.url}}},")

        lines.append("}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert citation to Markdown format."""
        parts = []

        # Title with link
        if self.url:
            parts.append(f"## [{self.title}]({self.url})")
        else:
            parts.append(f"## {self.title}")

        # Authors
        if self.authors:
            parts.append(f"**Authors:** {', '.join(self.authors)}")

        # Year
        if self.year:
            parts.append(f"**Year:** {self.year}")

        # IDs
        ids = []
        if self.arxiv_id:
            ids.append(f"arXiv: {self.arxiv_id}")
        if self.doi:
            ids.append(f"DOI: {self.doi}")
        if ids:
            parts.append("**IDs:** " + " | ".join(ids))

        # Verification
        parts.append(f"**Verification:** {self.verification_level.name}")

        # Abstract
        if self.abstract:
            parts.append(f"\n**Abstract:** {self.abstract[:500]}...")

        return "\n\n".join(parts)


class CitationVerifier:
    """Verify citations across multiple sources."""

    def __init__(
        self,
        s2_api_key: Optional[str] = None,
        arxiv_client=None,
        arxiv_base_url: str | None = None,
        semantic_scholar_client=None,
        cache_dir: Path | str | None = None,
        retry_attempts: int = 1,
        retry_backoff_seconds: float = 0.0,
        sleep_func: Callable[[float], None] = time.sleep,
    ):
        if arxiv_client is not None and arxiv_base_url:
            raise ValueError("arxiv_base_url cannot be used together with arxiv_client")
        if arxiv_client is None:
            from thesiskit.literature.arxiv import ArxivClient

            if arxiv_base_url:
                arxiv_client = ArxivClient(base_url=arxiv_base_url)
            else:
                arxiv_client = ArxivClient()
        if semantic_scholar_client is None:
            from thesiskit.literature.semanticscholar import SemanticScholarClient

            semantic_scholar_client = SemanticScholarClient(api_key=s2_api_key)

        self.arxiv = arxiv_client
        self.s2 = semantic_scholar_client
        self.cache = _MetadataCache(cache_dir) if cache_dir is not None else None
        self.retry_attempts = max(1, retry_attempts)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self._sleep = sleep_func

    def verify(self, citation: Citation) -> Citation:
        """Verify a citation and update its verification metadata."""
        return self.verify_with_report(citation).citation

    def verify_with_report(self, citation: Citation) -> VerificationResult:
        """Verify a citation and return auditable checks and issues.

        The verifier validates user-provided title, arXiv ID, DOI, and URL
        against source metadata when those fields are available. Missing fields
        may be filled from trusted sources, but mismatches are reported instead
        of being silently overwritten.
        """
        checks: list[VerificationCheck] = []
        issues: list[str] = []
        warnings: list[str] = []
        level = VerificationLevel.UNVERIFIED

        arxiv_paper = None
        arxiv_lookup = _MetadataLookupResult(None)
        arxiv_lookup_failed = False
        if citation.arxiv_id:
            arxiv_id = citation.arxiv_id
            try:
                arxiv_lookup = self._lookup_metadata(
                    source="arxiv",
                    key=arxiv_id,
                    fetcher=lambda: self.arxiv.get_paper(arxiv_id),
                )
                arxiv_paper = arxiv_lookup.paper
            except Exception as exc:  # pragma: no cover - defensive network guard
                arxiv_lookup_failed = True
                self._add_issue(
                    checks,
                    issues,
                    name="arxiv_id",
                    source="arxiv",
                    detail=(
                        f"arXiv lookup failed for arXiv:{citation.arxiv_id} "
                        f"after {self.retry_attempts} attempt(s): {exc}"
                    ),
                )
                arxiv_paper = None
            if arxiv_paper:
                source_note = " from cache" if arxiv_lookup.cache_hit else ""
                checks.append(
                    VerificationCheck(
                        name="arxiv_id",
                        source="arxiv",
                        passed=True,
                        detail=f"Found arXiv:{citation.arxiv_id}{source_note}",
                    )
                )
                level = VerificationLevel.ARXIV_VERIFIED
                self._fill_from_arxiv(citation, arxiv_paper)
                self._check_title(citation, arxiv_paper.get("title"), "arxiv", checks, issues)
                self._check_url(citation, arxiv_paper, checks, issues)
                self._check_doi(citation, arxiv_paper.get("doi"), "arxiv", checks, issues)
            elif not arxiv_lookup_failed:
                self._add_issue(
                    checks,
                    issues,
                    name="arxiv_id",
                    source="arxiv",
                    detail=f"arXiv:{citation.arxiv_id} was not found",
                )

        s2_paper = None
        s2_lookup = _MetadataLookupResult(None)
        lookup_id = self._semantic_scholar_lookup_id(citation)
        if lookup_id:
            try:
                s2_lookup = self._lookup_metadata(
                    source="semantic_scholar",
                    key=lookup_id,
                    fetcher=lambda: self.s2.get_paper(lookup_id),
                )
                s2_paper = s2_lookup.paper
            except Exception as exc:  # pragma: no cover - defensive network guard
                detail = self._semantic_scholar_lookup_warning(lookup_id, exc)
                checks.append(
                    VerificationCheck(
                        name="semantic_scholar",
                        source="semantic_scholar",
                        passed=False,
                        detail=detail,
                    )
                )
                warnings.append(detail)
            if s2_paper:
                source_note = " from cache" if s2_lookup.cache_hit else ""
                checks.append(
                    VerificationCheck(
                        name="semantic_scholar",
                        source="semantic_scholar",
                        passed=True,
                        detail=f"Found Semantic Scholar record for {lookup_id}{source_note}",
                    )
                )
                level = VerificationLevel.SEMANTIC_SCHOLAR_VERIFIED
                self._fill_from_semantic_scholar(citation, s2_paper)
                self._check_title(
                    citation,
                    s2_paper.get("title"),
                    "semantic_scholar",
                    checks,
                    issues,
                )
                external_ids = s2_paper.get("externalIds", {}) or {}
                self._check_doi(
                    citation,
                    external_ids.get("DOI"),
                    "semantic_scholar",
                    checks,
                    issues,
                )
                self._check_arxiv_id(citation, external_ids.get("ArXiv"), checks, issues)
                if not any(check.name == "url" and check.passed for check in checks):
                    self._check_semantic_scholar_url(citation, s2_paper, checks, issues)

        self._check_required_metadata_was_confirmed(citation, checks, issues)

        passed = len(issues) == 0 and any(check.passed for check in checks)
        if passed:
            level = VerificationLevel.FULLY_VERIFIED
        elif citation.doi and any(check.name == "doi" and check.passed for check in checks):
            level = max(level, VerificationLevel.DOI_VERIFIED, key=lambda item: item.value)

        citation.verification_level = level
        citation.verification_issues = issues
        return VerificationResult(
            citation=citation,
            passed=passed,
            level=level,
            checks=checks,
            issues=issues,
            warnings=warnings,
        )

    def close(self):
        """Close clients."""
        if hasattr(self.arxiv, "close"):
            self.arxiv.close()
        if hasattr(self.s2, "close"):
            self.s2.close()

    def _lookup_metadata(
        self,
        source: str,
        key: str,
        fetcher: Callable[[], Optional[dict]],
    ) -> _MetadataLookupResult:
        """Return metadata from cache or live source with retry/backoff."""
        if self.cache is not None:
            cached = self.cache.get(source, key)
            if cached is not None:
                return _MetadataLookupResult(paper=cached, cache_hit=True)

        last_exception: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                paper = fetcher()
            except Exception as exc:
                last_exception = exc
                if attempt < self.retry_attempts:
                    delay = self._retry_delay_seconds(exc, attempt)
                    if delay > 0:
                        self._sleep(delay)
                continue

            if self.cache is not None:
                self.cache.set(source, key, paper)
            return _MetadataLookupResult(paper=paper, cache_hit=False)

        if last_exception is not None:
            raise last_exception
        return _MetadataLookupResult(paper=None, cache_hit=False)

    def _retry_delay_seconds(self, exc: Exception, attempt: int) -> float:
        """Return retry delay, preferring HTTP Retry-After on rate limits."""
        retry_after = self._retry_after_seconds(exc)
        if retry_after is not None:
            return retry_after
        return self.retry_backoff_seconds * (2 ** (attempt - 1))

    def _retry_after_seconds(self, exc: Exception) -> Optional[float]:
        response = getattr(exc, "response", None)
        if getattr(response, "status_code", None) != 429:
            return None
        headers = getattr(response, "headers", {}) or {}
        value = headers.get("Retry-After") if hasattr(headers, "get") else None
        if not value:
            return None

        try:
            delay = float(value)
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(str(value))
            except (TypeError, ValueError, IndexError, OverflowError):
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            delay = (retry_at - datetime.now(timezone.utc)).total_seconds()

        if not math.isfinite(delay):
            return None
        return min(max(0.0, delay), 30.0)

    def _semantic_scholar_lookup_warning(self, lookup_id: str, exc: Exception) -> str:
        problem = "rate-limited" if self._exception_status_code(exc) == 429 else "unavailable"
        return (
            f"Semantic Scholar lookup {problem} for {lookup_id} "
            f"after {self.retry_attempts} attempt(s): {exc}"
        )

    def _exception_status_code(self, exc: Exception) -> Optional[int]:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        return status_code if isinstance(status_code, int) else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _fill_from_arxiv(self, citation: Citation, paper: dict) -> None:
        if not citation.title:
            citation.title = paper.get("title", "")
        if not citation.abstract:
            citation.abstract = paper.get("summary")
        if not citation.authors:
            citation.authors = paper.get("authors", [])
        if not citation.url:
            citation.url = paper.get("abs_url")

    def _fill_from_semantic_scholar(self, citation: Citation, paper: dict) -> None:
        citation.semantic_scholar_id = paper.get("paperId") or citation.semantic_scholar_id
        citation.citation_count = paper.get("citationCount", citation.citation_count)
        external_ids = paper.get("externalIds", {}) or {}
        if not citation.doi and external_ids.get("DOI"):
            citation.doi = external_ids["DOI"]

    def _semantic_scholar_lookup_id(self, citation: Citation) -> Optional[str]:
        if citation.semantic_scholar_id:
            return citation.semantic_scholar_id
        if citation.doi:
            return f"DOI:{citation.doi}"
        if citation.arxiv_id:
            return f"ARXIV:{citation.arxiv_id}"
        return None

    def _check_title(
        self,
        citation: Citation,
        source_title: Optional[str],
        source: str,
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        if not citation.title or not source_title:
            return
        passed = self._normalize_title(citation.title) == self._normalize_title(source_title)
        detail = f"expected={citation.title!r}; source={source_title!r}"
        checks.append(VerificationCheck("title", source, passed, detail))
        if not passed:
            issues.append(f"Title mismatch from {source}: {detail}")

    def _check_doi(
        self,
        citation: Citation,
        source_doi: Optional[str],
        source: str,
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        if not citation.doi or not source_doi:
            return
        passed = self._normalize_doi(citation.doi) == self._normalize_doi(source_doi)
        detail = f"expected={citation.doi!r}; source={source_doi!r}"
        checks.append(VerificationCheck("doi", source, passed, detail))
        if not passed:
            issues.append(f"DOI mismatch from {source}: {detail}")

    def _check_url(
        self,
        citation: Citation,
        arxiv_paper: dict,
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        if not citation.url:
            return
        allowed_urls = {
            arxiv_paper.get("abs_url"),
            arxiv_paper.get("pdf_url"),
        }
        if citation.arxiv_id:
            allowed_urls.update(
                {
                    f"https://arxiv.org/abs/{citation.arxiv_id}",
                    f"http://arxiv.org/abs/{citation.arxiv_id}",
                    f"https://arxiv.org/pdf/{citation.arxiv_id}",
                    f"http://arxiv.org/pdf/{citation.arxiv_id}",
                }
            )
        normalized_allowed = {self._normalize_url(url) for url in allowed_urls if url}
        passed = self._normalize_url(citation.url) in normalized_allowed
        detail = f"expected={citation.url!r}; allowed={sorted(normalized_allowed)!r}"
        checks.append(VerificationCheck("url", "arxiv", passed, detail))
        if not passed:
            issues.append(f"URL mismatch from arXiv: {detail}")

    def _check_semantic_scholar_url(
        self,
        citation: Citation,
        s2_paper: dict,
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        if not citation.url:
            return
        source_url = s2_paper.get("url")
        if not source_url:
            return
        passed = self._normalize_url(citation.url) == self._normalize_url(source_url)
        detail = f"expected={citation.url!r}; source={source_url!r}"
        checks.append(VerificationCheck("url", "semantic_scholar", passed, detail))
        if not passed:
            issues.append(f"URL mismatch from Semantic Scholar: {detail}")

    def _check_arxiv_id(
        self,
        citation: Citation,
        source_arxiv_id: Optional[str],
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        if not citation.arxiv_id or not source_arxiv_id:
            return
        passed = self._normalize_arxiv_id(citation.arxiv_id) == self._normalize_arxiv_id(
            source_arxiv_id
        )
        detail = f"expected={citation.arxiv_id!r}; source={source_arxiv_id!r}"
        checks.append(VerificationCheck("arxiv_id", "semantic_scholar", passed, detail))
        if not passed:
            issues.append(f"arXiv ID mismatch from Semantic Scholar: {detail}")

    def _check_required_metadata_was_confirmed(
        self,
        citation: Citation,
        checks: list[VerificationCheck],
        issues: list[str],
    ) -> None:
        passed_check_names = {check.name for check in checks if check.passed}
        if citation.title and "title" not in passed_check_names:
            issues.append("Title was not confirmed by arXiv or Semantic Scholar")
        if citation.doi and "doi" not in passed_check_names:
            issues.append("DOI was not confirmed by arXiv or Semantic Scholar")
        if citation.url and "url" not in passed_check_names:
            issues.append("URL was not confirmed by arXiv or Semantic Scholar")
        if citation.arxiv_id and "arxiv_id" not in passed_check_names:
            issues.append("arXiv ID was not confirmed by arXiv or Semantic Scholar")

    def _add_issue(
        self,
        checks: list[VerificationCheck],
        issues: list[str],
        name: str,
        source: str,
        detail: str,
    ) -> None:
        checks.append(VerificationCheck(name=name, source=source, passed=False, detail=detail))
        issues.append(detail)

    def _normalize_title(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _normalize_doi(self, value: str) -> str:
        return (
            value.strip()
            .lower()
            .removeprefix("https://doi.org/")
            .removeprefix("http://doi.org/")
            .removeprefix("doi:")
        )

    def _normalize_url(self, value: str) -> str:
        normalized = value.strip().replace("http://", "https://", 1).rstrip("/")
        return normalized.removesuffix(".pdf")

    def _normalize_arxiv_id(self, value: str) -> str:
        return value.strip().removeprefix("arXiv:").split("v")[0]


def citation_from_mapping(data: dict) -> Citation:
    """Build a Citation from a JSON-friendly metadata mapping."""
    title = str(data.get("title") or "").strip()
    if not title:
        raise ValueError("Citation entry is missing required field: title")

    authors = data.get("authors") or []
    normalized_authors = [
        author.get("name", "") if isinstance(author, dict) else str(author) for author in authors
    ]

    return Citation(
        title=title,
        authors=[author for author in normalized_authors if author],
        year=data.get("year"),
        arxiv_id=data.get("arxiv_id") or data.get("arxivId") or data.get("arxiv"),
        doi=data.get("doi"),
        semantic_scholar_id=data.get("semantic_scholar_id") or data.get("paperId"),
        url=data.get("url"),
        abstract=data.get("abstract") or data.get("abstract_excerpt"),
    )


def citation_to_mapping(citation: Citation) -> dict:
    """Convert a Citation into a stable JSON-friendly metadata mapping."""
    data: dict = {
        "title": citation.title,
        "authors": citation.authors,
    }
    optional_fields = {
        "year": citation.year,
        "arxiv_id": citation.arxiv_id,
        "doi": citation.doi,
        "semantic_scholar_id": citation.semantic_scholar_id,
        "url": citation.url,
        "abstract": citation.abstract,
        "citation_count": citation.citation_count,
    }
    data.update({key: value for key, value in optional_fields.items() if value is not None})
    return data


def load_citations_bibtex(path: Path | str) -> list[Citation]:
    """Load Citation objects from a BibTeX file.

    This intentionally supports the common subset ThesisKit exports and the
    mini-run example uses: title, author, year, eprint/archivePrefix, doi, and
    url. Unknown fields are ignored instead of making import brittle. Protective
    case braces such as `{NLP}` are stripped while TeX escape groups are kept.
    """
    source_path = Path(path)
    entries = _parse_bibtex_entries(source_path.read_text(encoding="utf-8"))
    citations: list[Citation] = []
    for _entry_type, _key, fields in entries:
        title = fields.get("title", "").strip()
        if not title:
            raise ValueError("BibTeX entry is missing required field: title")

        authors = [author.strip() for author in fields.get("author", "").split(" and ")]
        year = _parse_year(fields.get("year"))
        archive_prefix = fields.get("archiveprefix", "").lower()
        eprint = fields.get("eprint")
        arxiv_id = eprint if eprint and archive_prefix == "arxiv" else None
        citations.append(
            Citation(
                title=title,
                authors=[author for author in authors if author],
                year=year,
                arxiv_id=arxiv_id,
                doi=fields.get("doi"),
                url=fields.get("url"),
            )
        )
    return citations


def citations_to_bibtex(citations: list[Citation]) -> str:
    """Render citations as deterministic BibTeX text."""
    used_keys: set[str] = set()
    entries = []
    for index, citation in enumerate(citations, start=1):
        key = _bibtex_key(citation, index=index)
        base_key = key
        suffix = 2
        while key in used_keys:
            key = f"{base_key}{suffix}"
            suffix += 1
        used_keys.add(key)
        entries.append(citation.to_bibtex(key))
    return "\n\n".join(entries).rstrip() + "\n"


def write_citations_bibtex(citations: list[Citation], path: Path | str) -> None:
    """Write Citation objects to a UTF-8 BibTeX file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(citations_to_bibtex(citations), encoding="utf-8")


def write_citations_json(citations: list[Citation], path: Path | str) -> None:
    """Write Citation objects to a UTF-8 papers.json file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = [citation_to_mapping(citation) for citation in citations]
    destination.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_citations_json(path: Path | str) -> list[Citation]:
    """Load a list of Citation objects from a papers.json-style file."""
    source_path = Path(path)
    data = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Citation input must be a JSON list: {source_path}")
    return [citation_from_mapping(item) for item in data]


def verify_citations(
    citations: list[Citation],
    verifier: Optional[CitationVerifier] = None,
) -> list[VerificationResult]:
    """Verify citations and return auditable results."""
    owns_verifier = verifier is None
    if verifier is None:
        verifier = CitationVerifier()

    try:
        return [verifier.verify_with_report(citation) for citation in citations]
    finally:
        if owns_verifier and hasattr(verifier, "close"):
            verifier.close()


def render_verification_report(
    results: list[VerificationResult],
    source_path: Path | str | None = None,
) -> str:
    """Render citation verification results as an auditable Markdown report."""
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed
    warning_count = sum(len(result.warnings) for result in results)
    status = f"{passed} passed / {failed} failed"
    if warning_count:
        warning_label = "warning" if warning_count == 1 else "warnings"
        status = f"{status} / {warning_count} {warning_label}"

    lines = [
        "# Citation Verification Report",
        "",
    ]
    if source_path is not None:
        lines.extend([f"**Source file:** `{source_path}`", ""])
    lines.extend(
        [
            f"**Citations checked:** {total}",
            f"**Status:** {status}",
            "",
            "## Summary",
            "",
        ]
    )

    if not results:
        lines.extend(["No citations were provided.", ""])
        return "\n".join(lines).rstrip() + "\n"

    for result in results:
        icon = "❌" if not result.passed else "⚠️" if result.warnings else "✅"
        citation = result.citation
        ids = _citation_id_summary(citation)
        lines.append(f"- {icon} {citation.title} — {result.level.name}{ids}")

    lines.extend(["", "## Per-citation detail", ""])
    for index, result in enumerate(results, start=1):
        citation = result.citation
        icon = "❌" if not result.passed else "⚠️" if result.warnings else "✅"
        detail_status = (
            "failed"
            if not result.passed
            else "passed with warnings" if result.warnings else "passed"
        )
        lines.extend(
            [
                f"### [{index}] {icon} {citation.title}",
                "",
                f"- **Status:** {detail_status}",
                f"- **Verification level:** {result.level.name}",
            ]
        )
        if citation.authors:
            lines.append(f"- **Authors:** {', '.join(citation.authors)}")
        if citation.year:
            lines.append(f"- **Year:** {citation.year}")
        if citation.arxiv_id:
            lines.append(f"- **arXiv:** {citation.arxiv_id}")
        if citation.doi:
            lines.append(f"- **DOI:** {citation.doi}")
        if citation.url:
            lines.append(f"- **URL:** {citation.url}")

        lines.extend(["", "#### Checks", ""])
        if result.checks:
            for check in result.checks:
                check_status = "PASS" if check.passed else "FAIL"
                lines.append(f"- `{check.name} / {check.source}: {check_status}` — {check.detail}")
        else:
            lines.append("- No source checks were performed.")

        if result.warnings:
            lines.extend(["", "#### Warnings", ""])
            for warning in result.warnings:
                lines.append(f"- {warning}")

        lines.extend(["", "#### Issues", ""])
        if result.issues:
            for issue in result.issues:
                lines.append(f"- {issue}")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def verify_citations_json_file(
    input_path: Path | str,
    output_path: Path | str,
    verifier: Optional[CitationVerifier] = None,
) -> list[VerificationResult]:
    """Verify a citations JSON file and write a Markdown report."""
    citations = load_citations_json(input_path)
    results = verify_citations(citations, verifier=verifier)
    report = render_verification_report(results, source_path=Path(input_path))

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    return results


def _parse_bibtex_entries(text: str) -> list[tuple[str, str, dict[str, str]]]:
    """Parse BibTeX entries into entry type, key, and cleaned fields."""
    entries: list[tuple[str, str, dict[str, str]]] = []
    position = 0
    while True:
        at_position = text.find("@", position)
        if at_position == -1:
            break
        type_start = at_position + 1
        opener_position = _find_next_any(text, "{(", start=type_start)
        if opener_position == -1:
            break
        entry_type = text[type_start:opener_position].strip().lower()
        if entry_type in {"comment", "preamble", "string"}:
            position = opener_position + 1
            continue

        opener = text[opener_position]
        closer = "}" if opener == "{" else ")"
        body, position = _read_balanced(text, opener_position, opener, closer)
        key, fields_text = _split_key_and_fields(body)
        entries.append((entry_type, key, _parse_bibtex_fields(fields_text)))
    return entries


def _find_next_any(text: str, needles: str, start: int) -> int:
    positions = [text.find(needle, start) for needle in needles]
    positions = [position for position in positions if position != -1]
    return min(positions) if positions else -1


def _read_balanced(text: str, start: int, opener: str, closer: str) -> tuple[str, int]:
    depth = 0
    body_start = start + 1
    index = start
    while index < len(text):
        char = text[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[body_start:index], index + 1
        index += 1
    raise ValueError("Unclosed BibTeX entry")


def _split_key_and_fields(body: str) -> tuple[str, str]:
    comma = _find_top_level_comma(body)
    if comma == -1:
        return body.strip(), ""
    return body[:comma].strip(), body[comma + 1 :]


def _find_top_level_comma(text: str) -> int:
    depth = 0
    for index, char in enumerate(text):
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            return index
    return -1


def _parse_bibtex_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    position = 0
    while position < len(text):
        while position < len(text) and (text[position].isspace() or text[position] == ","):
            position += 1
        name_start = position
        while position < len(text) and (text[position].isalnum() or text[position] in "_-"):
            position += 1
        name = text[name_start:position].strip().lower()
        if not name:
            break
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text) or text[position] != "=":
            break
        position += 1
        while position < len(text) and text[position].isspace():
            position += 1
        value, position = _read_bibtex_value(text, position)
        fields[name] = _clean_bibtex_value(value)
    return fields


def _read_bibtex_value(text: str, start: int) -> tuple[str, int]:
    if start >= len(text):
        return "", start
    if text[start] == "{":
        return _read_balanced(text, start, "{", "}")
    if text[start] == '"':
        index = start + 1
        while index < len(text):
            if text[index] == '"' and text[index - 1] != "\\":
                return text[start + 1 : index], index + 1
            index += 1
        raise ValueError("Unclosed quoted BibTeX value")

    comma = text.find(",", start)
    if comma == -1:
        return text[start:].strip(), len(text)
    return text[start:comma].strip(), comma + 1


def _clean_bibtex_value(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip())
    return re.sub(r"\{([^{}\\]+)\}", r"\1", cleaned)


def _cache_path_part(value: str) -> str:
    """Make a source/cache key safe to use as one path component."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    if not safe:
        return "metadata"
    return safe[:160]


def _parse_year(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    match = re.search(r"\d{4}", value)
    return int(match.group(0)) if match else None


def _bibtex_key(citation: Citation, index: int) -> str:
    surname = "citation"
    if citation.authors:
        surname_tokens = re.findall(r"[A-Za-z0-9]+", citation.authors[0])
        if surname_tokens:
            surname = surname_tokens[-1].lower()
    year = str(citation.year or "noyear")
    title_tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", citation.title)]
    title_part = f"item{index}"
    if title_tokens:
        title_part = title_tokens[0]
        if title_part in {"a", "an", "and", "for", "in", "of", "on", "the", "to"}:
            title_part += title_tokens[1] if len(title_tokens) > 1 else ""
    return f"{surname}{year}{title_part}"


def _citation_id_summary(citation: Citation) -> str:
    ids = []
    if citation.arxiv_id:
        ids.append(f"arXiv:{citation.arxiv_id}")
    if citation.doi:
        ids.append(f"DOI:{citation.doi}")
    return f" ({'; '.join(ids)})" if ids else ""
