"""Tests for literature clients."""

import pytest
from unittest.mock import Mock, patch
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
    assert client.BASE_URL == "http://export.arxiv.org/api/query"
    client.close()
