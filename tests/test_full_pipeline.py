"""Test full pipeline execution."""

import pytest
from pathlib import Path
from thesiskit import run_full_pipeline, Config


@pytest.mark.integration
def test_full_pipeline_minimal(tmp_path):
    """Test minimal pipeline execution."""
    config = Config()
    config.llm.provider = "openai-compatible"
    config.llm.primary_model = "gpt-4o-mini"
    
    # Run with minimal topic
    result = run_full_pipeline(
        topic="Test topic",
        config=config,
        auto_approve=True,
        output_dir=tmp_path / "test_run",
    )
    
    assert result["run_id"].startswith("tk-")
    assert result["topic"] == "Test topic"
    assert len(result["stages"]) > 0
    assert result["final_status"] in ["completed", "partial"]


@pytest.mark.integration
def test_pipeline_stage_progression(tmp_path):
    """Test that stages progress in order."""
    from thesiskit.pipeline.stages import Stage
    
    config = Config()
    
    result = run_full_pipeline(
        topic="Test",
        config=config,
        auto_approve=True,
        output_dir=tmp_path / "progression_test",
    )
    
    # Check stages are in order
    stages = [s["stage"] for s in result["stages"]]
    assert stages == sorted(stages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
