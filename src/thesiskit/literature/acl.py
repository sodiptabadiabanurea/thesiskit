"""ACL Anthology client for exact-paper metadata lookups."""

from typing import Optional

import httpx

from thesiskit.literature.acl_ids import normalize_acl_id
from thesiskit.literature.citations import _parse_bibtex_entries, _parse_year


class ACLAnthologyClient:
    """Lightweight client for ACL Anthology paper BibTeX metadata.

    ACL Anthology's official data source is the public XML repository/Python API,
    but exact paper pages also expose stable ``<anthology-id>.bib`` endpoints.
    This client intentionally uses those lightweight endpoints to avoid pulling
    the full Anthology data repository into ThesisKit runtime installs.
    """

    BASE_URL = "https://aclanthology.org"

    def __init__(self, timeout: float = 30.0, base_url: str | None = None):
        self.base_url = (base_url if base_url is not None else self.BASE_URL).strip().rstrip("/")
        if not self.base_url:
            raise ValueError("base_url must not be blank")
        self.client = httpx.Client(timeout=timeout)

    def get_paper(self, acl_id: str) -> Optional[dict]:
        """Get one ACL Anthology paper by exact Anthology ID."""
        normalized_id = normalize_acl_id(acl_id)
        if not normalized_id:
            raise ValueError("acl_id must not be blank")

        try:
            response = self.client.get(f"{self.base_url}/{normalized_id}.bib")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

        entries = _parse_bibtex_entries(response.text)
        if not entries:
            return None
        entry_type, key, fields = entries[0]
        return _paper_from_bibtex(normalized_id, entry_type, key, fields)

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _paper_from_bibtex(
    acl_id: str,
    entry_type: str,
    key: str,
    fields: dict[str, str],
) -> dict:
    """Convert one ACL Anthology BibTeX entry into ThesisKit metadata."""
    known_fields = {
        "title",
        "author",
        "year",
        "journal",
        "booktitle",
        "publisher",
        "url",
        "doi",
        "abstract",
    }
    paper: dict = {
        "id": acl_id,
        "title": fields.get("title", ""),
        "authors": _parse_bibtex_authors(fields.get("author", "")),
        "year": _parse_year(fields.get("year")),
        "bibtex_key": key,
        "bibtex_entry_type": entry_type or "inproceedings",
        "bibtex_fields": {
            name: value for name, value in fields.items() if name not in known_fields and value
        },
    }
    for name in ["journal", "booktitle", "publisher", "url", "doi", "abstract"]:
        if fields.get(name):
            paper[name] = fields[name]
    return paper


def _parse_bibtex_authors(value: str) -> list[str]:
    """Convert BibTeX author strings into display names."""
    authors = []
    for raw_author in value.split(" and "):
        author = raw_author.strip()
        if not author:
            continue
        if "," in author:
            last, first = [part.strip() for part in author.split(",", 1)]
            author = f"{first} {last}".strip()
        authors.append(author)
    return authors
