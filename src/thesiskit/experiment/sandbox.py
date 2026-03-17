"""Experiment sandbox for running code safely."""

import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class ExperimentResult:
    """Result of experiment execution."""
    success: bool
    output: str
    error: Optional[str] = None
    metrics: Optional[dict] = None
    stdout: str = ""
    stderr: str = ""


class Sandbox:
    """Sandbox for executing experiment code."""
    
    def __init__(
        self,
        python_path: str = "python3",
        timeout: int = 300,
        max_memory_mb: int = 4096,
        workdir: Optional[Path] = None,
    ):
        self.python_path = python_path
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.workdir = workdir or Path(tempfile.mkdtemp(prefix="thesiskit_sandbox_"))
    
    def run(
        self,
        code: str,
        capture_output: bool = True,
    ) -> ExperimentResult:
        """Run code in sandbox.
        
        Args:
            code: Python code to execute
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            ExperimentResult with execution results
        """
        # Write code to temp file
        code_file = self.workdir / "experiment.py"
        code_file.write_text(code)
        
        try:
            # Run with resource limits
            result = subprocess.run(
                [self.python_path, str(code_file)],
                cwd=str(self.workdir),
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
            )
            
            # Check for errors
            if result.returncode != 0:
                return ExperimentResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            
            # Try to parse metrics from output
            metrics = None
            if "METRICS:" in result.stdout:
                try:
                    metrics_line = [
                        line for line in result.stdout.split("\n")
                        if line.startswith("METRICS:")
                    ][0]
                    metrics = json.loads(metrics_line[8:].strip())
                except (IndexError, json.JSONDecodeError):
                    pass
            
            return ExperimentResult(
                success=True,
                output=result.stdout,
                metrics=metrics,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        
        except subprocess.TimeoutExpired:
            return ExperimentResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.timeout}s",
            )
        
        except Exception as e:
            return ExperimentResult(
                success=False,
                output="",
                error=str(e),
            )
    
    def run_with_requirements(
        self,
        code: str,
        requirements: list[str],
    ) -> ExperimentResult:
        """Run code after installing requirements."""
        # Install requirements
        if requirements:
            pip_result = subprocess.run(
                [self.python_path.replace("python", "pip"), "install", "-q"] + requirements,
                capture_output=True,
                text=True,
            )
            
            if pip_result.returncode != 0:
                return ExperimentResult(
                    success=False,
                    output="",
                    error=f"Failed to install requirements: {pip_result.stderr}",
                )
        
        return self.run(code)
    
    def cleanup(self):
        """Clean up sandbox directory."""
        import shutil
        if self.workdir.exists():
            shutil.rmtree(self.workdir)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def check_code_safety(code: str) -> tuple[bool, str]:
    """Check if code is safe to run.
    
    Returns:
        Tuple of (is_safe, reason)
    """
    # Dangerous patterns
    dangerous = [
        "import os",
        "import subprocess",
        "import sys",
        "exec(",
        "eval(",
        "__import__",
        "open(",
        "file(",
        "input(",
        "raw_input(",
    ]
    
    for pattern in dangerous:
        if pattern in code:
            return False, f"Potentially dangerous pattern found: {pattern}"
    
    return True, "Code appears safe"
