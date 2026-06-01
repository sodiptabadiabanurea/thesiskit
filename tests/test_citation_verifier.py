"""Tests for citation verification reports."""

import json

from thesiskit.literature.citations import Citation, CitationVerifier, VerificationLevel


class FakeArxivClient:
    def __init__(self, paper):
        self.paper = paper
        self.requested_ids = []
        self.closed = False

    def get_paper(self, arxiv_id):
        self.requested_ids.append(arxiv_id)
        return self.paper

    def close(self):
        self.closed = True


class FakeSemanticScholarClient:
    def __init__(self, paper=None):
        self.paper = paper
        self.requested_ids = []
        self.closed = False

    def get_paper(self, lookup_id):
        self.requested_ids.append(lookup_id)
        return self.paper

    def close(self):
        self.closed = True


class RaisingArxivClient:
    def __init__(self):
        self.requested_ids = []

    def get_paper(self, arxiv_id):
        self.requested_ids.append(arxiv_id)
        raise RuntimeError(f"network unavailable for {arxiv_id}")

    def close(self):
        pass


class FlakyArxivClient:
    def __init__(self, paper, failures_before_success=1):
        self.paper = paper
        self.failures_before_success = failures_before_success
        self.requested_ids = []

    def get_paper(self, arxiv_id):
        self.requested_ids.append(arxiv_id)
        if len(self.requested_ids) <= self.failures_before_success:
            raise RuntimeError(f"temporary arXiv outage for {arxiv_id}")
        return self.paper

    def close(self):
        pass


RAG_ARXIV_PAPER = {
    "id": "2005.11401",
    "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    "authors": ["Patrick Lewis", "Ethan Perez"],
    "summary": "RAG paper abstract.",
    "abs_url": "https://arxiv.org/abs/2005.11401",
    "pdf_url": "https://arxiv.org/pdf/2005.11401",
    "doi": "10.48550/arXiv.2005.11401",
}

RAG_S2_PAPER = {
    "paperId": "abc123",
    "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    "citationCount": 999,
    "externalIds": {
        "ArXiv": "2005.11401",
        "DOI": "10.48550/arXiv.2005.11401",
    },
    "url": "https://www.semanticscholar.org/paper/abc123",
}


def test_verify_with_report_marks_matching_arxiv_doi_url_as_fully_verified():
    """Verifier should validate title, arXiv ID, DOI, and URL against sources."""
    verifier = CitationVerifier(
        arxiv_client=FakeArxivClient(RAG_ARXIV_PAPER),
        semantic_scholar_client=FakeSemanticScholarClient(RAG_S2_PAPER),
    )
    citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        arxiv_id="2005.11401",
        doi="10.48550/arXiv.2005.11401",
        url="https://arxiv.org/abs/2005.11401",
    )

    result = verifier.verify_with_report(citation)

    assert result.passed is True
    assert result.issues == []
    assert citation.verification_level == VerificationLevel.FULLY_VERIFIED
    assert citation.authors == ["Patrick Lewis", "Ethan Perez"]
    assert citation.citation_count == 999
    assert result.checks_by_name["arxiv_id"].passed is True
    assert result.checks_by_name["title"].passed is True
    assert result.checks_by_name["doi"].passed is True
    assert result.checks_by_name["url"].passed is True


def test_verify_with_report_reports_title_mismatch():
    """Verifier should not fully verify a citation whose title mismatches arXiv."""
    verifier = CitationVerifier(
        arxiv_client=FakeArxivClient(RAG_ARXIV_PAPER),
        semantic_scholar_client=FakeSemanticScholarClient(None),
    )
    citation = Citation(
        title="A Completely Different Paper",
        authors=[],
        arxiv_id="2005.11401",
        url="https://arxiv.org/abs/2005.11401",
    )

    result = verifier.verify_with_report(citation)

    assert result.passed is False
    assert citation.verification_level == VerificationLevel.ARXIV_VERIFIED
    assert any("title mismatch" in issue.lower() for issue in result.issues)
    assert result.checks_by_name["title"].passed is False


def test_verify_with_report_rejects_unconfirmed_non_arxiv_url():
    """A DOI/S2 citation should not pass with an arbitrary URL."""
    verifier = CitationVerifier(
        arxiv_client=FakeArxivClient(None),
        semantic_scholar_client=FakeSemanticScholarClient(RAG_S2_PAPER),
    )
    citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        doi="10.48550/arXiv.2005.11401",
        url="https://example.com/not-the-paper",
    )

    result = verifier.verify_with_report(citation)

    assert result.passed is False
    assert citation.verification_level == VerificationLevel.SEMANTIC_SCHOLAR_VERIFIED
    assert any("url" in issue.lower() for issue in result.issues)


def test_verify_with_report_returns_issue_when_arxiv_lookup_fails():
    """arXiv network errors should be reported, not raised."""
    verifier = CitationVerifier(
        arxiv_client=RaisingArxivClient(),
        semantic_scholar_client=FakeSemanticScholarClient(None),
    )
    citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        arxiv_id="2005.11401",
    )

    result = verifier.verify_with_report(citation)

    assert result.passed is False
    assert citation.verification_level == VerificationLevel.UNVERIFIED
    assert any("arxiv lookup failed" in issue.lower() for issue in result.issues)
    assert not any("was not found" in issue.lower() for issue in result.issues)


def test_verify_with_report_retries_transient_arxiv_failures_before_reporting_success():
    """Transient source errors should be retried before becoming report issues."""
    arxiv_client = FlakyArxivClient(RAG_ARXIV_PAPER, failures_before_success=1)
    verifier = CitationVerifier(
        arxiv_client=arxiv_client,
        semantic_scholar_client=FakeSemanticScholarClient(None),
        retry_attempts=2,
        retry_backoff_seconds=0,
    )
    citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        arxiv_id="2005.11401",
    )

    result = verifier.verify_with_report(citation)

    assert result.passed is True
    assert arxiv_client.requested_ids == ["2005.11401", "2005.11401"]
    assert not result.issues
    assert result.checks_by_name["arxiv_id"].passed is True


def test_verify_with_report_caches_arxiv_metadata_for_offline_reuse(tmp_path):
    """A successful lookup should be reused from local cache without another API call."""
    cache_dir = tmp_path / "metadata-cache"
    first_arxiv_client = FakeArxivClient(RAG_ARXIV_PAPER)
    first_verifier = CitationVerifier(
        arxiv_client=first_arxiv_client,
        semantic_scholar_client=FakeSemanticScholarClient(None),
        cache_dir=cache_dir,
    )
    citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        arxiv_id="2005.11401",
    )

    first_result = first_verifier.verify_with_report(citation)

    assert first_result.passed is True
    assert first_arxiv_client.requested_ids == ["2005.11401"]
    cache_files = list((cache_dir / "arxiv").glob("*.json"))
    assert len(cache_files) == 1
    assert json.loads(cache_files[0].read_text(encoding="utf-8"))["title"] == RAG_ARXIV_PAPER[
        "title"
    ]

    second_arxiv_client = RaisingArxivClient()
    second_verifier = CitationVerifier(
        arxiv_client=second_arxiv_client,
        semantic_scholar_client=FakeSemanticScholarClient(None),
        cache_dir=cache_dir,
    )
    second_citation = Citation(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=[],
        arxiv_id="2005.11401",
    )

    second_result = second_verifier.verify_with_report(second_citation)

    assert second_result.passed is True
    assert second_arxiv_client.requested_ids == []
    assert not second_result.issues
