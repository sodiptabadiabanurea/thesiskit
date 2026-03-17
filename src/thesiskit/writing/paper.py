"""Paper writing module."""

from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class PaperSection:
    """A section of a paper."""
    title: str
    content: str
    level: int = 1  # 1 = section, 2 = subsection, 3 = subsubsection


@dataclass
class Paper:
    """A research paper."""
    title: str
    authors: List[str]
    abstract: str
    sections: List[PaperSection]
    references: List[str]  # BibTeX keys
    
    def to_markdown(self) -> str:
        """Convert paper to Markdown."""
        lines = [f"# {self.title}", ""]
        
        # Authors
        lines.append(f"**Authors:** {', '.join(self.authors)}")
        lines.append("")
        
        # Abstract
        lines.append("## Abstract")
        lines.append(self.abstract)
        lines.append("")
        
        # Sections
        for section in self.sections:
            prefix = "#" * section.level
            lines.append(f"{prefix} {section.title}")
            lines.append(section.content)
            lines.append("")
        
        # References
        if self.references:
            lines.append("## References")
            for ref in self.references:
                lines.append(f"- {ref}")
        
        return "\n".join(lines)
    
    def to_latex(self, conference: str = "neurips_2025") -> str:
        """Convert paper to LaTeX."""
        from thesiskit.templates import generate_latex, markdown_to_latex
        
        # Build body
        body_parts = []
        for section in self.sections:
            prefix = "\\" + "sub" * (section.level - 1) + "section"
            if section.level == 1:
                prefix = "\\section"
            body_parts.append(f"{prefix}{{{section.title}}}")
            body_parts.append(markdown_to_latex(section.content))
        
        body = "\n\n".join(body_parts)
        
        return generate_latex(
            conference=conference,
            title=self.title,
            authors=" and ".join(self.authors),
            abstract=self.abstract,
            body=body,
        )
    
    def save(self, path: Path, format: str = "markdown") -> None:
        """Save paper to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            content = self.to_markdown()
        elif format == "latex":
            content = self.to_latex()
        else:
            raise ValueError(f"Unknown format: {format}")
        
        path.write_text(content)


class PaperBuilder:
    """Builder for creating papers."""
    
    def __init__(self):
        self.title = ""
        self.authors: List[str] = []
        self.abstract = ""
        self.sections: List[PaperSection] = []
        self.references: List[str] = []
    
    def set_title(self, title: str) -> "PaperBuilder":
        self.title = title
        return self
    
    def add_author(self, author: str) -> "PaperBuilder":
        self.authors.append(author)
        return self
    
    def set_abstract(self, abstract: str) -> "PaperBuilder":
        self.abstract = abstract
        return self
    
    def add_section(
        self,
        title: str,
        content: str,
        level: int = 1,
    ) -> "PaperBuilder":
        self.sections.append(PaperSection(title=title, content=content, level=level))
        return self
    
    def add_reference(self, bib_key: str) -> "PaperBuilder":
        self.references.append(bib_key)
        return self
    
    def build(self) -> Paper:
        if not self.title:
            raise ValueError("Title is required")
        if not self.authors:
            raise ValueError("At least one author is required")
        if not self.abstract:
            raise ValueError("Abstract is required")
        
        return Paper(
            title=self.title,
            authors=self.authors,
            abstract=self.abstract,
            sections=self.sections,
            references=self.references,
        )
