"""Tests for templates."""

from thesiskit.templates import Conference, generate_latex, markdown_to_latex


def test_conference_enum():
    """Test conference enum."""
    assert Conference.NEURIPS_2025.value == "neurips_2025"
    assert Conference.ICML_2026.value == "icml_2026"
    assert Conference.ICLR_2026.value == "iclr_2026"


def test_markdown_to_latex_headers():
    """Test Markdown header conversion."""
    md = "# Introduction\n## Methods\n### Details"
    latex = markdown_to_latex(md)
    
    assert r"\section*{Introduction}" in latex
    assert r"\section{Methods}" in latex
    assert r"\subsubsection{Details}" in latex


def test_markdown_to_latex_lists():
    """Test Markdown list conversion."""
    md = "- Item 1\n- Item 2\n- Item 3"
    latex = markdown_to_latex(md)
    
    assert r"\begin{itemize}" in latex
    assert r"\end{itemize}" in latex
    assert r"\item Item 1" in latex
    assert r"\item Item 2" in latex


def test_markdown_to_latex_formatting():
    """Test Markdown formatting conversion."""
    md = "This is **bold** and *italic* and `code`."
    latex = markdown_to_latex(md)
    
    assert r"\textbf{bold}" in latex
    assert r"\textit{italic}" in latex
    assert r"\texttt{code}" in latex
