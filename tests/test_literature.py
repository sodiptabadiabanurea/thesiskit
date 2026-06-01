"""Tests for literature clients."""

from unittest.mock import patch
from thesiskit.literature.arxiv import ArxivClient
from thesiskit.literature.citations import Citation, VerificationLevel


def test_citation_to_bibtex():
    """Test BibTeX generation."""
    citation = Citation(
        title="Test Paper",
        authors=["John Doe", "Jane Smith"],
        year=2024,
        arxiv_id="2401.12345",
        doi="10.1234/test",
    )
    
    bibtex = citation.to_bibtex("test2024")
    assert "@article{test2024," in bibtex
    assert "title = {Test Paper}" in bibtex
    assert "John Doe and Jane Smith" in bibtex
    assert "year = {2024}" in bibtex
    assert "eprint = {2401.12345}" in bibtex


def test_citation_to_markdown():
    """Test Markdown generation."""
    citation = Citation(
        title="Test Paper",
        authors=["John Doe"],
        year=2024,
        url="https://example.com/paper",
        abstract="This is a test abstract.",
    )
    
    md = citation.to_markdown()
    assert "# [Test Paper](https://example.com/paper)" in md
    assert "John Doe" in md
    assert "2024" in md


def test_verification_level():
    """Test verification level enum."""
    assert VerificationLevel.UNVERIFIED.value == 0
    assert VerificationLevel.FULLY_VERIFIED.value == 5


@patch("httpx.Client")
def test_arxiv_client_init(mock_client):
    """Test arXiv client initialization."""
    client = ArxivClient(timeout=60.0)
    assert client.BASE_URL == "https://export.arxiv.org/api/query"
    client.close()


@patch("httpx.Client")
def test_arxiv_client_uses_custom_base_url(mock_client):
    """Users should be able to route arXiv metadata through a cache proxy."""
    client = ArxivClient(base_url="https://arxiv-cache.example.workers.dev/api/query")
    mock_response = mock_client.return_value.get.return_value
    mock_response.text = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'

    client.search("id:2005.11401", max_results=1)

    mock_client.return_value.get.assert_called_once()
    called_url = mock_client.return_value.get.call_args.args[0]
    assert called_url == "https://arxiv-cache.example.workers.dev/api/query"
    assert mock_client.return_value.get.call_args.kwargs["params"]["search_query"] == "id:2005.11401"
    client.close()


@patch("httpx.Client")
def test_arxiv_client_rejects_blank_base_url(mock_client):
    """Whitespace-only proxy endpoints should fail fast before httpx sees them."""
    try:
        ArxivClient(base_url="   ")
    except ValueError as exc:
        assert "base_url" in str(exc)
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected blank base_url to raise ValueError")

    mock_client.assert_not_called()
