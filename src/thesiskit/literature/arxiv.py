"""ArXiv client for literature search."""

import httpx
from typing import Optional
from datetime import datetime


class ArxivClient:
    """Client for searching papers on arXiv."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(timeout=timeout)
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[dict]:
        """Search arXiv for papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort criterion (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)
            
        Returns:
            List of paper metadata dicts
        """
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        
        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        # Parse ATOM feed (simplified)
        papers = self._parse_feed(response.text)
        return papers
    
    def _parse_feed(self, xml: str) -> list[dict]:
        """Parse arXiv ATOM feed into structured data."""
        import xml.etree.ElementTree as ET
        
        papers = []
        root = ET.fromstring(xml)
        
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        
        for entry in root.findall("atom:entry", ns):
            paper = {
                "id": entry.find("atom:id", ns).text.split("/")[-1],
                "title": entry.find("atom:title", ns).text.strip(),
                "summary": entry.find("atom:summary", ns).text.strip(),
                "authors": [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)
                ],
                "published": entry.find("atom:published", ns).text,
                "updated": entry.find("atom:updated", ns).text,
                "pdf_url": None,
                "abs_url": entry.find("atom:id", ns).text,
                "categories": [
                    c.get("term")
                    for c in entry.findall("atom:category", ns)
                ],
            }
            
            # Find PDF link
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "application/pdf":
                    paper["pdf_url"] = link.get("href")
            
            papers.append(paper)
        
        return papers
    
    def get_paper(self, arxiv_id: str) -> Optional[dict]:
        """Get a specific paper by arXiv ID."""
        results = self.search(f"id:{arxiv_id}", max_results=1)
        return results[0] if results else None
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
