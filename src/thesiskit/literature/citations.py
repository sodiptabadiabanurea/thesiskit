"""Citation verification and management."""

import json
import re
from dataclasses import dataclass, field
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

    @property
    def checks_by_name(self) -> dict[str, VerificationCheck]:
        """Return the first check for each logical check name."""
        by_name: dict[str, VerificationCheck] = {}
        for check in self.checks:
            by_name.setdefault(check.name, check)
        return by_name


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
        semantic_scholar_client=None,
    ):
        if arxiv_client is None:
            from thesiskit.literature.arxiv import ArxivClient

            arxiv_client = ArxivClient()
        if semantic_scholar_client is None:
            from thesiskit.literature.semanticscholar import SemanticScholarClient

            semantic_scholar_client = SemanticScholarClient(api_key=s2_api_key)

        self.arxiv = arxiv_client
        self.s2 = semantic_scholar_client

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
        level = VerificationLevel.UNVERIFIED

        arxiv_paper = None
        arxiv_lookup_failed = False
        if citation.arxiv_id:
            try:
                arxiv_paper = self.arxiv.get_paper(citation.arxiv_id)
            except Exception as exc:  # pragma: no cover - defensive network guard
                arxiv_lookup_failed = True
                self._add_issue(
                    checks,
                    issues,
                    name="arxiv_id",
                    source="arxiv",
                    detail=f"arXiv lookup failed for arXiv:{citation.arxiv_id}: {exc}",
                )
                arxiv_paper = None
            if arxiv_paper:
                checks.append(
                    VerificationCheck(
                        name="arxiv_id",
                        source="arxiv",
                        passed=True,
                        detail=f"Found arXiv:{citation.arxiv_id}",
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
        lookup_id = self._semantic_scholar_lookup_id(citation)
        if lookup_id:
            try:
                s2_paper = self.s2.get_paper(lookup_id)
            except Exception as exc:  # pragma: no cover - defensive network guard
                issues.append(f"Semantic Scholar lookup failed for {lookup_id}: {exc}")
            if s2_paper:
                checks.append(
                    VerificationCheck(
                        name="semantic_scholar",
                        source="semantic_scholar",
                        passed=True,
                        detail=f"Found Semantic Scholar record for {lookup_id}",
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
        )

    def close(self):
        """Close clients."""
        if hasattr(self.arxiv, "close"):
            self.arxiv.close()
        if hasattr(self.s2, "close"):
            self.s2.close()

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
        author.get("name", "") if isinstance(author, dict) else str(author)
        for author in authors
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

    lines = [
        "# Citation Verification Report",
        "",
    ]
    if source_path is not None:
        lines.extend([f"**Source file:** `{source_path}`", ""])
    lines.extend(
        [
            f"**Citations checked:** {total}",
            f"**Status:** {passed} passed / {failed} failed",
            "",
            "## Summary",
            "",
        ]
    )

    if not results:
        lines.extend(["No citations were provided.", ""])
        return "\n".join(lines).rstrip() + "\n"

    for result in results:
        icon = "✅" if result.passed else "❌"
        citation = result.citation
        ids = _citation_id_summary(citation)
        lines.append(f"- {icon} {citation.title} — {result.level.name}{ids}")

    lines.extend(["", "## Per-citation detail", ""])
    for index, result in enumerate(results, start=1):
        citation = result.citation
        icon = "✅" if result.passed else "❌"
        lines.extend(
            [
                f"### [{index}] {icon} {citation.title}",
                "",
                f"- **Status:** {'passed' if result.passed else 'failed'}",
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
                lines.append(
                    f"- `{check.name} / {check.source}: {check_status}` — {check.detail}"
                )
        else:
            lines.append("- No source checks were performed.")

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


def _citation_id_summary(citation: Citation) -> str:
    ids = []
    if citation.arxiv_id:
        ids.append(f"arXiv:{citation.arxiv_id}")
    if citation.doi:
        ids.append(f"DOI:{citation.doi}")
    return f" ({'; '.join(ids)})" if ids else ""
