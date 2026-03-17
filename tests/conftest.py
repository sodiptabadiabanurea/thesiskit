"""Test configuration."""
import pytest
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "artifacts").mkdir()
    (project_dir / "references").mkdir()
    return project_dir


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample config file."""
    config_content = """
project:
  name: "test-project"

research:
  topic: "Test topic"

llm:
  provider: "openai-compatible"
  primary_model: "gpt-4o"
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    return config_path
