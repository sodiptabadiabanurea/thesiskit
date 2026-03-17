"""Configuration management for ThesisKit."""

from pathlib import Path
from typing import Optional, Literal
import os

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: Literal["openai-compatible", "anthropic", "acp"] = "openai-compatible"
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    api_key: Optional[str] = None
    primary_model: str = "gpt-4o"
    fallback_models: list[str] = Field(default_factory=lambda: ["gpt-4o-mini"])
    
    def get_api_key(self) -> str:
        """Get API key from env or config."""
        if self.api_key:
            return self.api_key
        return os.environ.get(self.api_key_env, "")


class SandboxConfig(BaseModel):
    """Sandbox execution configuration."""
    python_path: str = ".venv/bin/python"
    gpu_required: bool = False
    max_memory_mb: int = 4096
    allowed_imports: list[str] = Field(default_factory=lambda: [
        "math", "random", "json", "csv", "numpy", "torch", "sklearn"
    ])


class ExperimentConfig(BaseModel):
    """Experiment configuration."""
    mode: Literal["simulated", "sandbox", "docker"] = "sandbox"
    time_budget_sec: int = 300
    max_iterations: int = 10
    metric_key: str = "primary_metric"
    metric_direction: Literal["minimize", "maximize"] = "minimize"
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)


class ResearchConfig(BaseModel):
    """Research topic configuration."""
    topic: str = ""
    domains: list[str] = Field(default_factory=lambda: ["machine-learning"])
    daily_paper_count: int = 10
    quality_threshold: float = 4.0


class RuntimeConfig(BaseModel):
    """Runtime configuration."""
    timezone: str = "UTC"
    max_parallel_tasks: int = 3
    approval_timeout_hours: int = 12
    retry_limit: int = 2


class SecurityConfig(BaseModel):
    """Security configuration."""
    hitl_required_stages: list[int] = Field(default_factory=lambda: [5, 9, 20])
    allow_publish_without_approval: bool = False
    redact_sensitive_logs: bool = True


class Config(BaseModel):
    """Main configuration for ThesisKit."""
    project: dict = Field(default_factory=lambda: {"name": "my-research"})
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    experiment: ExperimentConfig = Field(default_factory=ExperimentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    @classmethod
    def from_yaml(cls, path: Path | str) -> "Config":
        """Load config from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        return cls(**data)
    
    def save_yaml(self, path: Path | str) -> None:
        """Save config to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


# Default config instance
default_config = Config()
