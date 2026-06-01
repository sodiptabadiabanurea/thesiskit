"""Tests for checked-in examples and demo artifacts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINI_RUN = ROOT / "examples" / "mini-run"


def test_mini_run_example_artifacts_are_complete():
    """The mini-run demo should be auditable from topic to final report."""
    required_files = [
        "README.md",
        "input/topic.txt",
        "citations/papers.json",
        "citations/verification_report.md",
        "citations/references.bib",
        "experiment/config.yaml",
        "experiment/results.json",
        "draft/paper.md",
        "verification/full_report.md",
    ]

    missing = [rel for rel in required_files if not (MINI_RUN / rel).is_file()]

    assert missing == []


def test_mini_run_papers_are_real_resolvable_citations():
    """Mini-run citations should include real IDs/URLs, not placeholder papers."""
    papers = json.loads((MINI_RUN / "citations" / "papers.json").read_text())

    assert len(papers) >= 3
    for paper in papers:
        assert paper["title"]
        assert paper["authors"]
        assert paper["year"] >= 2020
        assert paper["arxiv_id"]
        assert paper["url"].startswith("https://")
        assert "placeholder" not in paper["title"].lower()


def test_mini_run_experiment_records_reproducible_metrics():
    """Mini-run experiment results should record deterministic demo metrics."""
    results = json.loads((MINI_RUN / "experiment" / "results.json").read_text())

    assert results["dataset"] == "synthetic_rag_team_questions_v1"
    assert results["seed"] == 42
    assert (
        results["metrics"]["rag_answer_accuracy"] > results["metrics"]["baseline_answer_accuracy"]
    )
    assert results["metrics"]["citation_coverage"] >= 0.9
