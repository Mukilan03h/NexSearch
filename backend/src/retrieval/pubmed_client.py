"""
PubMed API client — biomedical and life sciences literature.
Scaffolded: enable via ENABLE_PUBMED=true in .env.
"""
from typing import List

from src.retrieval.base_retriever import BaseRetriever
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import Paper

logger = setup_logger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedClient(BaseRetriever):
    """
    PubMed / NCBI E-Utilities client.

    Covers 36M+ biomedical citations from MEDLINE, life science journals, and online books.
    Free to use; requires email for identification (optional API key for higher rate limits).

    TODO: Implement full search + efetch pipeline when enabled.
    """

    @property
    def source_name(self) -> str:
        return "pubmed"

    def is_available(self) -> bool:
        return settings.enable_pubmed

    def search(self, query: str, max_results: int = 20) -> List[Paper]:
        """
        Search PubMed for biomedical papers.

        Args:
            query: Search query (supports MeSH terms)
            max_results: Maximum results

        Returns:
            List of Paper objects
        """
        if not self.is_available():
            logger.debug("PubMed is disabled, skipping")
            return []

        logger.info(f"PubMed search not yet implemented: '{query}'")
        # TODO: Implement using E-Utilities:
        # 1. esearch.fcgi → get PubMed IDs
        # 2. efetch.fcgi → get full records
        # 3. Parse XML → Paper models
        return []
