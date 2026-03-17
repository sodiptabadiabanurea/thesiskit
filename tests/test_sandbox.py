"""Tests for experiment sandbox."""

import pytest
from thesiskit.experiment import Sandbox, check_code_safety


def test_check_code_safety_safe():
    """Test safety check for safe code."""
    code = "x = 1 + 2\nprint(x)"
    is_safe, reason = check_code_safety(code)
    assert is_safe is True


def test_check_code_safety_dangerous():
    """Test safety check for dangerous code."""
    code = "import os\nos.system('rm -rf /')"
    is_safe, reason = check_code_safety(code)
    assert is_safe is False
    assert "import os" in reason


def test_sandbox_run_simple():
    """Test sandbox simple execution."""
    with Sandbox() as sandbox:
        result = sandbox.run("print('Hello, World!')")
        assert result.success is True
        assert "Hello, World!" in result.output


def test_sandbox_run_with_error():
    """Test sandbox execution with error."""
    with Sandbox() as sandbox:
        result = sandbox.run("raise ValueError('test error')")
        assert result.success is False
        assert "ValueError" in result.error


def test_sandbox_timeout():
    """Test sandbox timeout."""
    with Sandbox(timeout=1) as sandbox:
        code = "import time\ntime.sleep(10)"
        result = sandbox.run(code)
        assert result.success is False
        assert "timed out" in result.error.lower()


def test_sandbox_metrics_extraction():
    """Test metrics extraction from output."""
    with Sandbox() as sandbox:
        code = "print('Result: 42')\nprint('METRICS: {\"accuracy\": 0.95}')"
        result = sandbox.run(code)
        assert result.success is True
        assert result.metrics is not None
        assert result.metrics["accuracy"] == 0.95
