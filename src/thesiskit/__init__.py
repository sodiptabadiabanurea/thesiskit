"""ThesisKit — Everything you need to ship academic research."""

__version__ = "0.1.0"

from thesiskit.pipeline.runner import run_pipeline
from thesiskit.config import Config

__all__ = ["run_pipeline", "Config", "__version__"]
