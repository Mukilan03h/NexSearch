"""
Abstract base class for all data retrieval providers.
New providers (PubMed, OpenAlex, etc.) implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List

from models.schemas import Paper


class BaseRetriever(ABC):
    """Abstract interface for academic paper data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier (e.g., 'arxiv', 'semantic_scholar')."""
        ...

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> List[Paper]:
        """
        Search for academic papers.

        Args:
            query: Search query string
            max_results: Maximum number of papers to return

        Returns:
            List of normalized Paper objects
        """
        ...

    def is_available(self) -> bool:
        """Check if this retriever is configured and available."""
        return True
