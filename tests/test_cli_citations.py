"""Tests for citation verification CLI/report generation."""

import json
from pathlib import Path

from thesiskit.cli import main
from thesiskit.literature.citations import (
    Citation,
    VerificationCheck,
    VerificationLevel,
    VerificationResult,
    load_citations_json,
    render_verification_report,
)


class RecordingVerifier:
    """Deterministic verifier for CLI tests without network calls."""

    def __init__(self):
        self.seen_titles: list[str] = []
        self.closed = False

    def verify_with_report(self, citation: Citation) -> VerificationResult:
        self.seen_titles.append(citation.title)
        passed = "Broken" not in citation.title
        issues = [] if passed else ["Title was not confirmed by arXiv or Semantic Scholar"]
        level = VerificationLevel.FULLY_VERIFIED if passed else VerificationLevel.UNVERIFIED
        citation.verification_level = level
        citation.verification_issues = issues
        return VerificationResult(
            citation=citation,
            passed=passed,
            level=level,
            checks=[
                VerificationCheck(
                    name="title",
                    source="test-double",
                    passed=passed,
                    detail=f"checked {citation.title}",
                )
            ],
            issues=issues,
        )

    def close(self):
        self.closed = True


def test_load_citations_json_maps_mini_run_fields(tmp_path):
    """papers.json entries should become Citation objects while ignoring extra metadata."""
    papers_path = tmp_path / "papers.json"
    papers_path.write_text(
        json.dumps(
            [
                {
                    "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                    "authors": ["Patrick Lewis", "Ethan Perez"],
                    "year": 2020,
                    "arxiv_id": "2005.11401",
                    "doi": "10.48550/arXiv.2005.11401",
                    "url": "https://arxiv.org/abs/2005.11401",
                    "semantic_scholar_id": "abc123",
                    "abstract_excerpt": "RAG combines parametric and non-parametric memory.",
                    "venue": "NeurIPS 2020",
                }
            ]
        )
    )

    citations = load_citations_json(papers_path)

    assert citations == [
        Citation(
            title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
            authors=["Patrick Lewis", "Ethan Perez"],
            year=2020,
            arxiv_id="2005.11401",
            doi="10.48550/arXiv.2005.11401",
            semantic_scholar_id="abc123",
            url="https://arxiv.org/abs/2005.11401",
            abstract="RAG combines parametric and non-parametric memory.",
        )
    ]


def test_load_citations_json_requires_titles(tmp_path):
    """Citation inputs should fail fast before rendering anonymous report rows."""
    papers_path = tmp_path / "papers.json"
    papers_path.write_text(json.dumps([{"authors": ["A"], "arxiv_id": "1234.56789"}]))

    try:
        load_citations_json(papers_path)
    except ValueError as exc:
        assert "title" in str(exc).lower()
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected missing title to raise ValueError")


def test_render_verification_report_summarizes_checks_and_issues():
    """Markdown reports should be auditable without reading Python objects."""
    good = Citation(title="Verified Paper", authors=["A"], arxiv_id="1234.56789")
    bad = Citation(title="Broken Paper", authors=[], arxiv_id="9999.00000")
    results = [
        VerificationResult(
            citation=good,
            passed=True,
            level=VerificationLevel.FULLY_VERIFIED,
            checks=[VerificationCheck("arxiv_id", "arxiv", True, "Found arXiv:1234.56789")],
            issues=[],
        ),
        VerificationResult(
            citation=bad,
            passed=False,
            level=VerificationLevel.UNVERIFIED,
            checks=[VerificationCheck("arxiv_id", "arxiv", False, "arXiv:9999.00000 was not found")],
            issues=["arXiv:9999.00000 was not found"],
        ),
    ]

    report = render_verification_report(results, source_path=Path("citations/papers.json"))

    assert report.startswith("# Citation Verification Report")
    assert "**Source file:** `citations/papers.json`" in report
    assert "**Citations checked:** 2" in report
    assert "**Status:** 1 passed / 1 failed" in report
    assert "✅ Verified Paper" in report
    assert "❌ Broken Paper" in report
    assert "arxiv_id / arxiv: PASS" in report
    assert "arxiv_id / arxiv: FAIL" in report
    assert "arXiv:9999.00000 was not found" in report


def test_citations_verify_cli_writes_report_and_returns_failure_for_failed_citations(tmp_path):
    """`thesiskit citations verify` should write the report and fail closed on issues."""
    papers_path = tmp_path / "papers.json"
    report_path = tmp_path / "verification_report.md"
    papers_path.write_text(
        json.dumps(
            [
                {"title": "Verified Paper", "authors": ["A"], "arxiv_id": "1234.56789"},
                {"title": "Broken Paper", "authors": ["B"], "arxiv_id": "9999.00000"},
            ]
        )
    )
    verifier = RecordingVerifier()

    exit_code = main(
        [
            "citations",
            "verify",
            "--input",
            str(papers_path),
            "--output",
            str(report_path),
        ],
        verifier_factory=lambda: verifier,
    )

    assert exit_code == 1
    assert verifier.seen_titles == ["Verified Paper", "Broken Paper"]
    assert verifier.closed is True
    assert report_path.is_file()
    report = report_path.read_text()
    assert "**Status:** 1 passed / 1 failed" in report
    assert "Title was not confirmed" in report


def test_citations_verify_cli_can_allow_known_failures(tmp_path):
    """Users may generate an audit report without making a nonzero CLI exit mandatory."""
    papers_path = tmp_path / "papers.json"
    report_path = tmp_path / "verification_report.md"
    papers_path.write_text(
        json.dumps([{"title": "Broken Paper", "authors": [], "arxiv_id": "9999.00000"}])
    )

    exit_code = main(
        [
            "citations",
            "verify",
            "--input",
            str(papers_path),
            "--output",
            str(report_path),
            "--allow-failures",
        ],
        verifier_factory=RecordingVerifier,
    )

    assert exit_code == 0
    assert "❌ Broken Paper" in report_path.read_text()


def test_citations_verify_cli_returns_failure_for_missing_input(tmp_path):
    """Missing citation input should be a clean CLI failure, not a traceback."""
    exit_code = main(
        [
            "citations",
            "verify",
            "--input",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "verification_report.md"),
        ],
        verifier_factory=RecordingVerifier,
    )

    assert exit_code == 1
    assert not (tmp_path / "verification_report.md").exists()


def test_citations_verify_cli_passes_cache_and_retry_options_to_verifier(tmp_path):
    """CLI users should be able to make live verification cache-backed and retry-safe."""
    papers_path = tmp_path / "papers.json"
    report_path = tmp_path / "verification_report.md"
    cache_dir = tmp_path / "metadata-cache"
    papers_path.write_text(
        json.dumps([{"title": "Verified Paper", "authors": ["A"], "arxiv_id": "1234.56789"}])
    )
    captured_kwargs = {}

    def verifier_factory(**kwargs):
        captured_kwargs.update(kwargs)
        return RecordingVerifier()

    exit_code = main(
        [
            "citations",
            "verify",
            "--input",
            str(papers_path),
            "--output",
            str(report_path),
            "--cache-dir",
            str(cache_dir),
            "--retry-attempts",
            "4",
            "--retry-backoff",
            "0.25",
            "--arxiv-base-url",
            "https://arxiv-cache.example.workers.dev/api/query",
        ],
        verifier_factory=verifier_factory,
    )

    assert exit_code == 0
    assert captured_kwargs["cache_dir"] == cache_dir
    assert captured_kwargs["retry_attempts"] == 4
    assert captured_kwargs["retry_backoff_seconds"] == 0.25
    assert captured_kwargs["arxiv_base_url"] == "https://arxiv-cache.example.workers.dev/api/query"
    assert report_path.is_file()
