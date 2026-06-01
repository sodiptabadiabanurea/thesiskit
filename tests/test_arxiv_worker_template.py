"""Tests for the Cloudflare Worker arXiv cache proxy template."""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER_TEMPLATE = PROJECT_ROOT / "workers" / "arxiv-cache-proxy.js"


def test_arxiv_worker_template_caches_query_api_only():
    """The worker template should cache arXiv metadata queries without proxying PDFs."""
    source = WORKER_TEMPLATE.read_text(encoding="utf-8")

    assert "https://export.arxiv.org/api/query" in source
    assert "caches.default" in source
    assert "Cache-Control" in source
    assert "application/atom+xml" in source
    assert "PDF proxying is intentionally not supported" in source
    assert "searchParams.sort" in source


def test_arxiv_worker_template_has_polite_rate_limit_guardrails():
    """The worker should document that it reduces duplicate requests, not evades limits."""
    source = WORKER_TEMPLATE.read_text(encoding="utf-8")

    assert "Do not use this worker to exceed arXiv API limits" in source
    assert "one request every three seconds" in source
    assert "single connection" in source
    assert "User-Agent" in source
    assert "Cache-Control" in source
    assert "no-store" in source


def test_arxiv_worker_template_is_valid_javascript():
    """A checked-in worker template should parse before users deploy it."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    source = WORKER_TEMPLATE.read_text(encoding="utf-8")
    completed = subprocess.run(
        [node, "--check", "--input-type=module"],
        input=source,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
