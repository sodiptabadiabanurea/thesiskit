"""Tests for ACL Anthology citation source support."""

from pathlib import Path
from unittest.mock import Mock, patch

from thesiskit.literature.acl import ACLAnthologyClient
from thesiskit.literature.citations import (
    Citation,
    CitationVerifier,
    VerificationLevel,
    citation_from_mapping,
    citation_to_mapping,
    load_citations_bibtex,
    write_citations_bibtex,
)

ACL_BIBTEX = """@inproceedings{kitaev-etal-2022-learned,
  title = {Learned Incremental Representations for Parsing},
  author = {Kitaev, Nikita and Lu, Thomas and Klein, Dan},
  booktitle = {Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year = {2022},
  publisher = {Association for Computational Linguistics},
  url = {https://aclanthology.org/2022.acl-long.220/},
  doi = {10.18653/v1/2022.acl-long.220},
  pages = {3086--3095}
}
"""


@patch("httpx.Client")
def test_acl_anthology_client_fetches_bibtex_by_id(mock_client):
    """The lightweight ACL client should fetch exact Anthology IDs as BibTeX."""
    response = Mock()
    response.text = ACL_BIBTEX
    mock_client.return_value.get.return_value = response

    client = ACLAnthologyClient(base_url="https://acl.example")
    paper = client.get_paper("2022.acl-long.220")

    mock_client.return_value.get.assert_called_once_with(
        "https://acl.example/2022.acl-long.220.bib"
    )
    response.raise_for_status.assert_called_once()
    assert paper == {
        "id": "2022.acl-long.220",
        "title": "Learned Incremental Representations for Parsing",
        "authors": ["Nikita Kitaev", "Thomas Lu", "Dan Klein"],
        "year": 2022,
        "booktitle": "Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
        "publisher": "Association for Computational Linguistics",
        "url": "https://aclanthology.org/2022.acl-long.220/",
        "doi": "10.18653/v1/2022.acl-long.220",
        "bibtex_key": "kitaev-etal-2022-learned",
        "bibtex_entry_type": "inproceedings",
        "bibtex_fields": {"pages": "3086--3095"},
    }
    client.close()


@patch("httpx.Client")
def test_acl_anthology_client_normalizes_urls_and_rejects_unsafe_ids(mock_client):
    """ACL IDs should preserve case while rejecting path/query injection."""
    response = Mock()
    response.text = ACL_BIBTEX.replace("2022.acl-long.220", "P19-1017")
    mock_client.return_value.get.return_value = response

    client = ACLAnthologyClient(base_url="https://acl.example")
    client.get_paper("https://aclanthology.org/P19-1017/?utm_source=test")

    mock_client.return_value.get.assert_called_once_with("https://acl.example/P19-1017.bib")

    mock_client.return_value.get.reset_mock()
    try:
        client.get_paper("../P19-1017")
    except ValueError as exc:
        assert "ACL Anthology ID" in str(exc)
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected unsafe ACL ID to raise ValueError")
    mock_client.return_value.get.assert_not_called()
    client.close()


def test_acl_id_round_trips_through_mapping_and_bibtex(tmp_path: Path):
    """ACL Anthology IDs should survive JSON mapping and BibTeX import/export."""
    citation = citation_from_mapping(
        {
            "title": "Learned Incremental Representations for Parsing",
            "authors": ["Nikita Kitaev"],
            "year": 2022,
            "acl_anthology_id": "2022.acl-long.220",
        }
    )

    assert citation.acl_id == "2022.acl-long.220"
    assert citation_to_mapping(citation)["acl_id"] == "2022.acl-long.220"

    path = tmp_path / "references.bib"
    write_citations_bibtex([citation], path)
    bibtex = path.read_text(encoding="utf-8")
    assert "aclid = {2022.acl-long.220}" in bibtex

    loaded = load_citations_bibtex(path)
    assert loaded[0].acl_id == "2022.acl-long.220"


class FakeACLClient:
    def __init__(self, paper):
        self.paper = paper
        self.calls = []
        self.closed = False

    def get_paper(self, acl_id):
        self.calls.append(acl_id)
        return self.paper

    def close(self):
        self.closed = True


class FakeSemanticScholarClient:
    def __init__(self, paper):
        self.paper = paper
        self.calls = []

    def get_paper(self, lookup_id):
        self.calls.append(lookup_id)
        return self.paper

    def close(self):
        pass


class EmptyClient:
    def close(self):
        pass


def test_citation_verifier_derives_case_sensitive_acl_id_from_doi():
    """Legacy ACL IDs embedded in DOI suffixes should keep their original case."""
    acl = FakeACLClient(
        {
            "id": "P19-1017",
            "title": "A Legacy ACL Paper",
            "authors": ["Ada Researcher"],
            "year": 2019,
            "url": "https://aclanthology.org/P19-1017/",
            "doi": "10.18653/v1/P19-1017",
        }
    )
    citation = Citation(
        title="A Legacy ACL Paper",
        authors=[],
        doi="10.18653/v1/P19-1017",
    )
    verifier = CitationVerifier(
        arxiv_client=EmptyClient(),
        semantic_scholar_client=EmptyClient(),
        acl_anthology_client=acl,
    )

    result = verifier.verify_with_report(citation)

    assert acl.calls == ["P19-1017"]
    assert result.passed is True
    assert citation.acl_id == "P19-1017"


def test_acl_confirmation_prevents_semantic_scholar_url_false_failure():
    """S2 has its own canonical URL, so ACL-confirmed URLs must not fail later."""
    s2 = FakeSemanticScholarClient(
        {
            "paperId": "30a4754062a5f8c99e665db0b702a4da060af340",
            "title": "Learned Incremental Representations for Parsing",
            "url": "https://www.semanticscholar.org/paper/30a4754062a5f8c99e665db0b702a4da060af340",
            "externalIds": {"DOI": "10.18653/v1/2022.acl-long.220"},
        }
    )
    acl = FakeACLClient(
        {
            "id": "2022.acl-long.220",
            "title": "Learned Incremental Representations for Parsing",
            "authors": ["Nikita Kitaev", "Thomas Lu", "Dan Klein"],
            "year": 2022,
            "url": "https://aclanthology.org/2022.acl-long.220/",
            "doi": "10.18653/v1/2022.acl-long.220",
        }
    )
    citation = Citation(
        title="Learned Incremental Representations for Parsing",
        authors=[],
        doi="10.18653/v1/2022.acl-long.220",
        url="https://aclanthology.org/2022.acl-long.220",
    )
    verifier = CitationVerifier(
        arxiv_client=EmptyClient(),
        semantic_scholar_client=s2,
        acl_anthology_client=acl,
    )

    result = verifier.verify_with_report(citation)

    assert s2.calls == ["DOI:10.18653/v1/2022.acl-long.220"]
    assert acl.calls == ["2022.acl-long.220"]
    assert result.passed is True
    assert result.issues == []
    url_checks = [check for check in result.checks if check.name == "url"]
    assert any(check.source == "acl_anthology" and check.passed for check in url_checks)


def test_citation_verifier_uses_acl_anthology_source():
    """Verifier should confirm title/DOI/URL from ACL Anthology metadata."""
    acl = FakeACLClient(
        {
            "id": "2022.acl-long.220",
            "title": "Learned Incremental Representations for Parsing",
            "authors": ["Nikita Kitaev", "Thomas Lu", "Dan Klein"],
            "year": 2022,
            "booktitle": "Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
            "publisher": "Association for Computational Linguistics",
            "url": "https://aclanthology.org/2022.acl-long.220/",
            "doi": "10.18653/v1/2022.acl-long.220",
            "bibtex_key": "kitaev-etal-2022-learned",
            "bibtex_entry_type": "inproceedings",
            "bibtex_fields": {"pages": "3086--3095"},
        }
    )
    citation = Citation(
        title="Learned Incremental Representations for Parsing",
        authors=[],
        acl_id="2022.acl-long.220",
        doi="10.18653/v1/2022.acl-long.220",
        url="https://aclanthology.org/2022.acl-long.220",
    )
    verifier = CitationVerifier(
        arxiv_client=EmptyClient(),
        semantic_scholar_client=EmptyClient(),
        acl_anthology_client=acl,
    )

    result = verifier.verify_with_report(citation)

    assert acl.calls == ["2022.acl-long.220"]
    assert result.passed is True
    assert result.level == VerificationLevel.FULLY_VERIFIED
    assert result.issues == []
    assert result.checks_by_name["acl_id"].passed is True
    assert result.checks_by_name["title"].source == "acl_anthology"
    assert result.checks_by_name["doi"].source == "acl_anthology"
    assert result.checks_by_name["url"].source == "acl_anthology"
    assert citation.authors == ["Nikita Kitaev", "Thomas Lu", "Dan Klein"]
    assert citation.booktitle.startswith("Proceedings of the 60th Annual Meeting")
    assert citation.bibtex_entry_type == "inproceedings"
    assert citation.bibtex_fields == {"pages": "3086--3095"}
