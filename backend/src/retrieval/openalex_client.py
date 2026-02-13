"""
OpenAlex API client — broad cross-domain academic search.
Scaffolded: enable via ENABLE_OPENALEX=true in .env.
"""
from typing import List

from src.retrieval.base_retriever import BaseRetriever
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import Paper

logger = setup_logger(__name__)

BASE_URL = "https://api.openalex.org"


class OpenAlexClient(BaseRetriever):
    """
    OpenAlex API client.

    Covers 250M+ works across all disciplines.
    Completely free, no API key required.
    Polite pool: include mailto in requests for higher rate limits.

    TODO: Implement full search when enabled.
    """

    @property
    def source_name(self) -> str:
        return "openalex"

    def is_available(self) -> bool:
        return settings.enable_openalex

    def search(self, query: str, max_results: int = 20) -> List[Paper]:
        """
        Search OpenAlex for academic works.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of Paper objects
        """
        if not self.is_available():
            logger.debug("OpenAlex is disabled, skipping")
            return []

        logger.info(f"OpenAlex search not yet implemented: '{query}'")
        # TODO: Implement using works endpoint:
        # GET https://api.openalex.org/works?search={query}&per_page={max_results}
        # Parse response → Paper models
        return []
