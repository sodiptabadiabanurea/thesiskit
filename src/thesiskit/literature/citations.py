"""Citation verification and management."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class VerificationLevel(Enum):
    """Citation verification levels."""
    UNVERIFIED = 0
    ARXIV_VERIFIED = 1
    DOI_VERIFIED = 2
    SEMANTIC_SCHOLAR_VERIFIED = 3
    LLM_RELEVANCE_CHECKED = 4
    FULLY_VERIFIED = 5


@dataclass
class Citation:
    """A verified citation."""
    title: str
    authors: list[str]
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    verification_level: VerificationLevel = VerificationLevel.UNVERIFIED
    relevance_score: Optional[float] = None
    
    def to_bibtex(self, key: str) -> str:
        """Convert citation to BibTeX format."""
        lines = [f"@article{{{key},"]
        lines.append(f"  title = {{{self.title}}},")
        
        if self.authors:
            authors_str = " and ".join(self.authors)
            lines.append(f"  author = {{{authors_str}}},")
        
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        
        if self.arxiv_id:
            lines.append(f"  eprint = {{{self.arxiv_id}}},")
            lines.append(f"  archiveprefix = {{arXiv}},")
        
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        
        if self.url:
            lines.append(f"  url = {{{self.url}}},")
        
        lines.append("}")
        return "\n".join(lines)
    
    def to_markdown(self) -> str:
        """Convert citation to Markdown format."""
        parts = []
        
        # Title with link
        if self.url:
            parts.append(f"## [{self.title}]({self.url})")
        else:
            parts.append(f"## {self.title}")
        
        # Authors
        if self.authors:
            parts.append(f"**Authors:** {', '.join(self.authors)}")
        
        # Year
        if self.year:
            parts.append(f"**Year:** {self.year}")
        
        # IDs
        ids = []
        if self.arxiv_id:
            ids.append(f"arXiv: {self.arxiv_id}")
        if self.doi:
            ids.append(f"DOI: {self.doi}")
        if ids:
            parts.append("**IDs:** " + " | ".join(ids))
        
        # Verification
        parts.append(f"**Verification:** {self.verification_level.name}")
        
        # Abstract
        if self.abstract:
            parts.append(f"\n**Abstract:** {self.abstract[:500]}...")
        
        return "\n\n".join(parts)


class CitationVerifier:
    """Verify citations across multiple sources."""
    
    def __init__(self, s2_api_key: Optional[str] = None):
        from thesiskit.literature.arxiv import ArxivClient
        from thesiskit.literature.semanticscholar import SemanticScholarClient
        
        self.arxiv = ArxivClient()
        self.s2 = SemanticScholarClient(api_key=s2_api_key)
    
    def verify(self, citation: Citation) -> Citation:
        """Verify a citation across sources.
        
        Updates verification level based on what sources confirm the citation.
        """
        level = VerificationLevel.UNVERIFIED
        
        # Check arXiv
        if citation.arxiv_id:
            arxiv_paper = self.arxiv.get_paper(citation.arxiv_id)
            if arxiv_paper:
                level = VerificationLevel.ARXIV_VERIFIED
                # Fill in missing data
                if not citation.title:
                    citation.title = arxiv_paper["title"]
                if not citation.abstract:
                    citation.abstract = arxiv_paper["summary"]
                if not citation.authors:
                    citation.authors = arxiv_paper["authors"]
        
        # Check Semantic Scholar
        if citation.doi or citation.arxiv_id or citation.semantic_scholar_id:
            lookup_id = (
                citation.semantic_scholar_id
                or f"DOI:{citation.doi}"
                or f"ARXIV:{citation.arxiv_id}"
            )
            
            try:
                s2_paper = self.s2.get_paper(lookup_id)
                if s2_paper:
                    level = VerificationLevel.SEMANTIC_SCHOLAR_VERIFIED
                    citation.semantic_scholar_id = s2_paper.get("paperId")
                    citation.citation_count = s2_paper.get("citationCount", 0)
                    
                    # Fill missing data
                    if not citation.doi and s2_paper.get("externalIds", {}).get("DOI"):
                        citation.doi = s2_paper["externalIds"]["DOI"]
            except Exception:
                pass
        
        citation.verification_level = level
        return citation
    
    def close(self):
        """Close clients."""
        self.arxiv.close()
        self.s2.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
