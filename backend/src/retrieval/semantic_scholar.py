"""
Semantic Scholar API client — cross-domain academic paper retrieval.
Scaffolded: enable via ENABLE_SEMANTIC_SCHOLAR=true in .env.
"""
from typing import List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.retrieval.base_retriever import BaseRetriever
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import Paper

logger = setup_logger(__name__)

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "paperId,title,authors,abstract,year,citationCount,externalIds,url,openAccessPdf"


class SemanticScholarClient(BaseRetriever):
    """
    Semantic Scholar API client.

    Covers 200M+ papers across all disciplines.
    Free tier: 100 requests/5 minutes; API key for higher limits.
    """

    def __init__(self):
        self.api_key = settings.semantic_scholar_api_key
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key
        logger.info("SemanticScholarClient initialized")

    @property
    def source_name(self) -> str:
        return "semantic_scholar"

    def is_available(self) -> bool:
        return settings.enable_semantic_scholar

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
    def search(self, query: str, max_results: int = 20) -> List[Paper]:
        """
        Search Semantic Scholar for papers.

        Args:
            query: Search query
            max_results: Max results (API limit: 100 per request)

        Returns:
            List of normalized Paper objects
        """
        if not self.is_available():
            logger.debug("Semantic Scholar is disabled, skipping")
            return []

        logger.info(f"Searching Semantic Scholar: '{query}' (max={max_results})")

        try:
            resp = requests.get(
                f"{BASE_URL}/paper/search",
                params={"query": query, "limit": min(max_results, 100), "fields": FIELDS},
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            papers = []
            for item in data.get("data", []):
                paper = self._parse_result(item)
                if paper:
                    papers.append(paper)

            logger.info(f"Retrieved {len(papers)} papers from Semantic Scholar")
            return papers

        except requests.RequestException as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            raise

    def _parse_result(self, item: dict) -> Optional[Paper]:
        """Convert Semantic Scholar result to Paper model."""
        try:
            # Extract authors
            authors = [a.get("name", "Unknown") for a in item.get("authors", [])]

            # Extract PDF URL from openAccessPdf
            pdf_url = None
            if item.get("openAccessPdf"):
                pdf_url = item["openAccessPdf"].get("url")

            # Extract DOI
            doi = None
            ext_ids = item.get("externalIds", {})
            if ext_ids:
                doi = ext_ids.get("DOI")

            from datetime import datetime
            year = item.get("year") or 2024
            pub_date = datetime(year, 1, 1)

            return Paper(
                id=item.get("paperId", "unknown"),
                title=item.get("title", "Untitled"),
                authors=authors,
                abstract=item.get("abstract") or "No abstract available.",
                published_date=pub_date,
                url=item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                source="semantic_scholar",
                citations=item.get("citationCount"),
                pdf_url=pdf_url,
                doi=doi,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Semantic Scholar result: {e}")
            return None
