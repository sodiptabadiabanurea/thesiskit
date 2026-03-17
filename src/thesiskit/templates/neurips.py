"""NeurIPS 2025 LaTeX template."""

NEURIPS_2025_TEMPLATE = r"""
\documentclass{article}

% Packages
\usepackage{neurips_2025}
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

\bibliographystyle{plain}
\bibliography{references}

\end{document}
"""


def generate_neurips_latex(
    title: str,
    authors: str,
    abstract: str,
    body: str,
) -> str:
    """Generate NeurIPS 2025 LaTeX from content.
    
    Args:
        title: Paper title
        authors: Author string
        abstract: Abstract text
        body: Main body (sections, etc.)
        
    Returns:
        Complete LaTeX document
    """
    return NEURIPS_2025_TEMPLATE.format(
        title=title,
        authors=authors,
        abstract=abstract,
        body=body,
    )
