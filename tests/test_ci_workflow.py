"""Tests for GitHub Actions CI workflow."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_runs_project_quality_gates():
    """CI should run the same gates used before merging local work."""
    workflow = CI_WORKFLOW.read_text()

    for expected in [
        "python -m ruff check .",
        "python -m pytest -q",
        "python -m build",
        "python -m twine check dist/*",
        'python -m thesiskit.cli example mini-run --output "$tmpdir/mini-run"',
        "python -m thesiskit.cli citations verify",
        "python -m thesiskit.cli citations export-bibtex",
        "python -m thesiskit.cli citations import-bibtex",
        '--input "$tmpdir/mini-run/citations/papers.json"',
        '--output "$tmpdir/generated-verification-report.md"',
        '--cache-dir "$tmpdir/metadata-cache"',
        "--retry-attempts 2",
        "--allow-failures",
    ]:
        assert expected in workflow


def test_ci_workflow_exercises_supported_python_versions():
    """CI should cover the Python versions advertised in pyproject.toml."""
    workflow = CI_WORKFLOW.read_text()

    for version in ["3.10", "3.11", "3.12"]:
        assert version in workflow
