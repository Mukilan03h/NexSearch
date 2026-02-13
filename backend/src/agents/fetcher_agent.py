"""
Fetcher Agent — queries multiple data sources and collects papers.
Uses the retriever factory to dynamically select enabled providers.
"""
from typing import List, Optional

import requests

from src.agents.base_agent import BaseAgent
from src.retrieval.retriever_factory import get_retrievers, get_retriever_by_name
from src.storage.minio_client import MinIOClient
from src.utils.logger import setup_logger
from models.schemas import Paper, SearchPlan

logger = setup_logger(__name__)


class FetcherAgent(BaseAgent):
    """
    Fetches papers from all enabled data sources, deduplicates,
    and optionally stores PDFs in MinIO.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.minio: Optional[MinIOClient] = None

    def _get_minio(self) -> MinIOClient:
        """Lazy-init MinIO client."""
        if self.minio is None:
            try:
                self.minio = MinIOClient()
                self.minio.ensure_buckets()
            except Exception as e:
                self.logger.warning(f"MinIO not available: {e}")
        return self.minio

    def execute(self, plan: SearchPlan) -> List[Paper]:
        """Alias for fetch_papers."""
        return self.fetch_papers(plan)

    def fetch_papers(self, plan: SearchPlan) -> List[Paper]:
        """
        Fetch papers from all sources specified in the search plan.

        Args:
            plan: SearchPlan with keywords, sources, and parameters

        Returns:
            Deduplicated list of Paper objects
        """
        self.logger.info(
            f"Fetching papers: keywords={plan.keywords}, sources={plan.sources}, max={plan.max_papers}"
        )

        all_papers: List[Paper] = []
        query = " ".join(plan.keywords)

        # Fetch from each specified source
        for source_name in plan.sources:
            try:
                retriever = get_retriever_by_name(source_name)
                if not retriever.is_available():
                    self.logger.debug(f"Skipping disabled source: {source_name}")
                    continue

                papers = retriever.search(query, max_results=plan.max_papers)
                self.logger.info(f"Fetched {len(papers)} papers from {source_name}")
                all_papers.extend(papers)

            except Exception as e:
                self.logger.error(f"Failed to fetch from {source_name}: {e}")
                continue

        # If no results from specified sources, try all enabled retrievers
        if not all_papers:
            self.logger.warning("No results from specified sources, trying all enabled retrievers")
            for retriever in get_retrievers():
                try:
                    papers = retriever.search(query, max_results=plan.max_papers)
                    all_papers.extend(papers)
                except Exception as e:
                    self.logger.error(f"Failed to fetch from {retriever.source_name}: {e}")

        # Deduplicate by paper ID
        unique = self._deduplicate(all_papers)
        self.logger.info(f"Total unique papers: {len(unique)} (from {len(all_papers)} raw)")

        # Try to store PDFs in MinIO
        self._store_pdfs(unique)

        return unique

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers by ID."""
        seen = set()
        unique = []
        for p in papers:
            if p.id not in seen:
                seen.add(p.id)
                unique.append(p)
        return unique

    def _store_pdfs(self, papers: List[Paper]) -> None:
        """Download and store PDFs in MinIO (best-effort)."""
        minio = self._get_minio()
        if minio is None:
            return

        stored = 0
        for paper in papers:
            if not paper.pdf_url:
                continue
            try:
                resp = requests.get(paper.pdf_url, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    minio.upload_pdf(paper.id, resp.content)
                    stored += 1
            except Exception as e:
                self.logger.debug(f"PDF download skipped for {paper.id}: {e}")

        if stored > 0:
            self.logger.info(f"Stored {stored} PDFs in MinIO")
