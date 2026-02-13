"""
ArXiv API client — primary data source for academic papers.
Features: retry logic, polite rate limiting, TTL caching.
"""
import time
from typing import List, Optional

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cachetools import TTLCache

from src.retrieval.base_retriever import BaseRetriever
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import Paper

logger = setup_logger(__name__)

# Module-level cache: up to 100 queries, 24-hour TTL
_cache: TTLCache = TTLCache(maxsize=100, ttl=settings.cache_ttl_hours * 3600)


class ArxivClient(BaseRetriever):
    """
    Production-ready arXiv client with retry, caching, and polite delays.

    arXiv covers: CS, Physics, Math, Stats, EE, Econ, Q-Bio, Q-Finance.
    """

    def __init__(self):
        self.max_results = settings.arxiv_max_results
        self.delay = settings.arxiv_delay_seconds
        logger.info(f"ArxivClient initialized (max_results={self.max_results}, delay={self.delay}s)")

    @property
    def source_name(self) -> str:
        return "arxiv"

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type((Exception,)),
    )
    def search(self, query: str, max_results: Optional[int] = None) -> List[Paper]:
        """
        Search arXiv for academic papers.

        Args:
            query: Search query (supports arXiv syntax: ti:, au:, cat:, abs:)
            max_results: Override default max results

        Returns:
            List of Paper objects normalized from arXiv results
        """
        max_results = max_results or self.max_results
        cache_key = f"arxiv:{query}:{max_results}"

        # Check cache
        if settings.enable_caching and cache_key in _cache:
            cached = _cache[cache_key]
            logger.info(f"Cache hit for arXiv query: '{query}' ({len(cached)} papers)")
            return cached

        logger.info(f"Searching arXiv: '{query}' (max={max_results})")

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers = []
        for i, result in enumerate(search.results()):
            paper = self._parse_result(result)
            papers.append(paper)

            # Polite delay between requests (except last)
            if i < max_results - 1:
                time.sleep(self.delay)

        # Cache results
        if settings.enable_caching:
            _cache[cache_key] = papers

        logger.info(f"Retrieved {len(papers)} papers from arXiv")
        return papers

    def search_by_category(self, category: str = "cs.AI", max_results: Optional[int] = None) -> List[Paper]:
        """Search within a specific arXiv category."""
        return self.search(f"cat:{category}", max_results)

    def _parse_result(self, result: arxiv.Result) -> Paper:
        """Convert arXiv API result to normalized Paper model."""
        return Paper(
            id=result.get_short_id(),
            title=result.title.strip(),
            authors=[author.name for author in result.authors],
            abstract=result.summary.strip(),
            published_date=result.published,
            url=result.entry_id,
            source="arxiv",
            pdf_url=result.pdf_url,
            doi=result.doi,
        )
