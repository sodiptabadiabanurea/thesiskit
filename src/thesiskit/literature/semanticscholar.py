"""Semantic Scholar client for literature search."""

import httpx
from typing import Optional


class SemanticScholarClient:
    """Client for Semantic Scholar API."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.client = httpx.Client(timeout=timeout)
        self.api_key = api_key
        if api_key:
            self.client.headers["x-api-key"] = api_key
    
    def search(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[list[str]] = None,
    ) -> list[dict]:
        """Search Semantic Scholar for papers.
        
        Args:
            query: Search query
            limit: Maximum number of results
            fields: Fields to return (default: basic fields)
            
        Returns:
            List of paper metadata dicts
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "authors",
                "year",
                "citationCount",
                "referenceCount",
                "url",
                "externalIds",
            ]
        
        response = self.client.get(
            f"{self.BASE_URL}/paper/search",
            params={
                "query": query,
                "limit": limit,
                "fields": ",".join(fields),
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
    
    def get_paper(self, paper_id: str, fields: Optional[list[str]] = None) -> Optional[dict]:
        """Get a specific paper by ID.
        
        Args:
            paper_id: Semantic Scholar paper ID or external ID (DOI, arXiv, etc.)
            fields: Fields to return
            
        Returns:
            Paper metadata or None if not found
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "authors",
                "year",
                "citationCount",
                "referenceCount",
                "url",
                "externalIds",
                "citations",
                "references",
            ]
        
        try:
            response = self.client.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": ",".join(fields)},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_references(self, paper_id: str, limit: int = 100) -> list[dict]:
        """Get papers cited by a given paper."""
        response = self.client.get(
            f"{self.BASE_URL}/paper/{paper_id}/references",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json().get("data", [])
    
    def get_citations(self, paper_id: str, limit: int = 100) -> list[dict]:
        """Get papers that cite a given paper."""
        response = self.client.get(
            f"{self.BASE_URL}/paper/{paper_id}/citations",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json().get("data", [])
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
