"""Tests for ThesisKit config."""

import pytest
from thesiskit.config import Config, LLMConfig, ExperimentConfig


def test_default_config():
    """Test default config creation."""
    config = Config()
    assert config.project["name"] == "my-research"
    assert config.llm.provider == "openai-compatible"
    assert config.experiment.mode == "sandbox"


def test_llm_config():
    """Test LLM config."""
    llm = LLMConfig(
        provider="openai-compatible",
        base_url="https://api.openai.com/v1",
        primary_model="gpt-4o",
    )
    assert llm.provider == "openai-compatible"
    assert llm.primary_model == "gpt-4o"


def test_config_from_dict():
    """Test creating config from dict."""
    data = {
        "project": {"name": "test-project"},
        "llm": {"provider": "openai-compatible", "primary_model": "gpt-4o"},
    }
    config = Config.from_dict(data)
    assert config.project["name"] == "test-project"
    assert config.llm.provider == "openai-compatible"


def test_config_save_load(tmp_path):
    """Test saving and loading config."""
    config = Config(project={"name": "test"})
    config_path = tmp_path / "config.yaml"
    
    config.save_yaml(config_path)
    assert config_path.exists()
    
    loaded = Config.from_yaml(config_path)
    assert loaded.project["name"] == "test"
