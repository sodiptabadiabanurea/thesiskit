"""Tests for the deterministic pipeline runner."""

import json

from thesiskit.config import Config
from thesiskit.pipeline.runner import run_pipeline
from thesiskit.pipeline.stages import Stage


def test_run_pipeline_executes_all_stages_and_writes_artifacts(tmp_path):
    """Auto-approved runs should execute every stage and persist auditable artifacts."""
    config = Config()

    result = run_pipeline(
        config=config,
        topic="retrieval augmented generation evaluation",
        auto_approve=True,
        output_dir=tmp_path / "run",
    )

    assert result["topic"] == "retrieval augmented generation evaluation"
    assert result["final_status"] == "completed"
    assert [stage["stage"] for stage in result["stages"]] == [stage.value for stage in Stage]
    assert {stage["status"] for stage in result["stages"]} == {"done"}
    assert all(stage["artifact"] for stage in result["stages"])
    assert all((tmp_path / "run" / stage["artifact"]).is_file() for stage in result["stages"])

    topic_artifact = json.loads(
        (tmp_path / "run" / result["stages"][0]["artifact"]).read_text(encoding="utf-8")
    )
    codegen_artifact = json.loads(
        (tmp_path / "run" / result["stages"][9]["artifact"]).read_text(encoding="utf-8")
    )
    experiment_artifact = json.loads(
        (tmp_path / "run" / result["stages"][11]["artifact"]).read_text(encoding="utf-8")
    )
    assert topic_artifact["outputs"]["terms"] == [
        "retrieval",
        "augmented",
        "generation",
        "evaluation",
    ]
    assert codegen_artifact["outputs"]["metric_key"] == "primary_metric"
    assert experiment_artifact["outputs"]["results"] == {
        "primary_metric": 1.0,
        "status": "simulated",
    }

    summary_path = tmp_path / "run" / "pipeline_summary.json"
    assert summary_path.is_file()
    assert json.loads(summary_path.read_text(encoding="utf-8")) == result


def test_run_pipeline_blocks_at_first_gate_without_auto_approval(tmp_path):
    """Non-approved runs should stop deterministically at the first human gate."""
    config = Config()
    config.research.topic = "controllable text generation"

    result = run_pipeline(
        config=config,
        auto_approve=False,
        output_dir=tmp_path / "run",
    )

    assert result["final_status"] == "blocked"
    assert [stage["stage"] for stage in result["stages"]] == [1, 2, 3, 4, 5]
    blocked_stage = result["stages"][-1]
    assert blocked_stage["stage"] == Stage.LITERATURE_SCREEN.value
    assert blocked_stage["status"] == "blocked"
    assert blocked_stage["requires_approval"] is True
    assert blocked_stage["approved"] is False
    blocked_artifact = json.loads(
        (tmp_path / "run" / blocked_stage["artifact"]).read_text(encoding="utf-8")
    )
    assert blocked_artifact["status"] == "blocked"
    assert blocked_artifact["message"].startswith("Stage requires human approval")
    assert (tmp_path / "run" / blocked_stage["artifact"]).is_file()


def test_run_pipeline_requires_topic(tmp_path):
    """The deterministic runner should fail fast when no topic is available."""
    config = Config()

    try:
        run_pipeline(config=config, output_dir=tmp_path / "run")
    except ValueError as exc:
        assert "topic" in str(exc).lower()
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected missing topic to raise ValueError")
