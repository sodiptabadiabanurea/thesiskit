"""Conference template management."""

from enum import Enum
from typing import Callable, Optional

# Lazy imports to_neurips_generator = None
_icml_generator = None


class Conference(str, Enum):
    """Supported conference templates."""
    NEURIPS_2025 = "neurips_2025"
    ICML_2026 = "icml_2026"
    ICLR_2026 = "iclr_2026"


def _get_neurips_generator():
    """Lazy load NeurIPS generator."""
    global _neurips_generator
    if _neurips_generator is None:
        try:
            from thesiskit.templates.neurips import generate_neurips_latex
            _neurips_generator = generate_neurips_latex
        except ImportError:
            pass
    return _neurips_generator


def _get_icml_generator():
    """Lazy load ICML generator."""
    global _icml_generator
    if _icml_generator is None:
        try:
            from thesiskit.templates.icml import generate_icml_latex
            _icml_generator = generate_icml_latex
        except ImportError:
            pass
    return _icml_generator


def get_template(conference: Conference) -> Optional[Callable]:
    """Get template generator for conference."""
    generators = {
        Conference.NEURIPS_2025: _get_neurips_generator(),
        Conference.ICML_2026: _get_icml_generator(),
    }
    return generators.get(conference)


def generate_latex(
    conference: Conference,
    title: str,
    authors: str,
    abstract: str,
    body: str,
) -> str:
    """Generate LaTeX for a specific conference.
    
    Args:
        conference: Target conference
        title: Paper title
        authors: Author string
        abstract: Abstract text
        body: Main body
        
    Returns:
        Complete LaTeX document
        
    Raises:
        ValueError: If conference is not supported
    """
    generator = get_template(conference)
    if not generator:
        raise ValueError(f"Unsupported conference: {conference}")
    
    return generator(title, authors, abstract, body)


def markdown_to_latex(md: str) -> str:
    """Convert Markdown to LaTeX.
    
    Simple conversion for common elements:
    - Headers → sections
    - Bold → textbf
    - Italic → textit
    - Code → texttt
    - Lists → itemize
    """
    lines = md.split("\n")
    latex_lines = []
    
    in_list = False
    
    for line in lines:
        # Headers
        if line.startswith("### "):
            if in_list:
                latex_lines.append(r"\end{itemize}")
                in_list = False
            latex_lines.append(r"\subsubsection{" + line[4:] + "}")
        elif line.startswith("## "):
            if in_list:
                latex_lines.append(r"\end{itemize}")
                in_list = False
            latex_lines.append(r"\section{" + line[3:] + "}")
        elif line.startswith("# "):
            if in_list:
                latex_lines.append(r"\end{itemize}")
                in_list = False
            latex_lines.append(r"\section*{" + line[2:] + "}")
        # Lists
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                latex_lines.append(r"\begin{itemize}")
                in_list = True
            latex_lines.append(r"\item " + line[2:])
        # Empty lines
        elif not line.strip():
            if in_list:
                latex_lines.append(r"\end{itemize}")
                in_list = False
            latex_lines.append("")
        # Regular text
        else:
            if in_list:
                latex_lines.append(r"\end{itemize}")
                in_list = False
            # Basic formatting
            text = line
            text = text.replace("**", r"\textbf{", 1).replace("**", "}", 1)
            text = text.replace("*", r"\textit{", 1).replace("*", "}", 1)
            text = text.replace("`", r"\texttt{", 1).replace("`", "}", 1)
            latex_lines.append(text)
    
    if in_list:
        latex_lines.append(r"\end{itemize}")
    
    return "\n".join(latex_lines)
