"""ICML 2026 LaTeX template."""

ICML_2026_TEMPLATE = r"""
\documentclass{article}

% Packages
\usepackage{icml2026}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\usepackage{url}
\usepackage{booktabs}
\usepackage{amsfonts}
\usepackage{nicefrac}
\usepackage{microtype}
\usepackage{graphicx}

% Title
\title{{{title}}}

% Authors
\author{{{authors}}}

\begin{document}

\maketitle

\begin{abstract}
{abstract}
\end{abstract}

{body}

\bibliographystyle{icml2026}
\bibliography{references}

\end{document}
"""


def generate_icml_latex(
    title: str,
    authors: str,
    abstract: str,
    body: str,
) -> str:
    """Generate ICML 2026 LaTeX from content.
    
    Args:
        title: Paper title
        authors: Author string
        abstract: Abstract text
        body: Main body (sections, etc.)
        
    Returns:
        Complete LaTeX document
    """
    return ICML_2026_TEMPLATE.format(
        title=title,
        authors=authors,
        abstract=abstract,
        body=body,
    )
