"""Tests for reproducible example CLI commands."""

import subprocess
import sys
from pathlib import Path

import pytest

from thesiskit.cli import copy_mini_run_example


ROOT = Path(__file__).resolve().parents[1]


def test_cli_copies_mini_run_example(tmp_path):
    """`thesiskit example mini-run` should copy the auditable demo artifacts."""
    output_dir = tmp_path / "mini-run-copy"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "thesiskit.cli",
            "example",
            "mini-run",
            "--output",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (output_dir / "input" / "topic.txt").is_file()
    assert (output_dir / "citations" / "papers.json").is_file()
    assert (output_dir / "experiment" / "results.json").is_file()
    assert (output_dir / "draft" / "paper.md").is_file()
    assert "Copied mini-run example" in result.stdout


def test_copy_mini_run_example_refuses_to_overwrite_non_example_directory(tmp_path):
    """--overwrite should not recursively delete arbitrary user directories."""
    output_dir = tmp_path / "artifacts"
    output_dir.mkdir()
    (output_dir / "notes.txt").write_text("do not delete")

    with pytest.raises(FileExistsError, match="not a ThesisKit mini-run"):
        copy_mini_run_example(output_dir, overwrite=True)

    assert (output_dir / "notes.txt").read_text() == "do not delete"
