"""Helpers for ACL Anthology ID extraction and validation."""

import re
from urllib.parse import unquote, urlsplit

_ACL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_ACL_DOI_PREFIX_RE = re.compile(r"^(?:https?://doi\.org/|doi:)?10\.18653/v1/", re.IGNORECASE)


def normalize_acl_id(value: str | None) -> str:
    """Return a safe ACL Anthology ID from an ID or ACL URL.

    The ACL Anthology endpoint is path-based (``/<paper-id>.bib``), so this
    helper accepts only plain ID characters after URL/path cleanup. It preserves
    case because legacy IDs such as ``P19-1017`` are case-sensitive upstream.
    """
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    parsed = urlsplit(text)
    if parsed.scheme or parsed.netloc:
        text = parsed.path

    text = unquote(text).strip().strip("/")
    for suffix in (".bib", ".pdf"):
        if text.lower().endswith(suffix):
            text = text[: -len(suffix)]
            break
    text = text.strip("/")

    if not text:
        return ""
    if ".." in text or not _ACL_ID_RE.fullmatch(text):
        raise ValueError(
            "ACL Anthology ID must be a plain Anthology paper ID, "
            "for example '2022.acl-long.220' or 'P19-1017'"
        )
    return text


def acl_id_from_doi(value: str | None) -> str | None:
    """Extract a case-preserving ACL Anthology ID from an ACL DOI."""
    if value is None:
        return None

    text = str(value).strip()
    match = _ACL_DOI_PREFIX_RE.match(text)
    if not match:
        return None
    return normalize_acl_id(text[match.end() :])
