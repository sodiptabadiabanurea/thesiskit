"""ThesisKit — Everything you need to ship academic research."""

__version__ = "0.4.0"

from thesiskit.pipeline.runner import run_pipeline
from thesiskit.pipeline.full_pipeline import run_full_pipeline, Pipeline
from thesiskit.config import Config

__all__ = ["run_pipeline", "run_full_pipeline", "Pipeline", "Config", "__version__"]
