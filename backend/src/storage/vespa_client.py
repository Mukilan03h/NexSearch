"""
Vespa client for vector search and document indexing.
Provides hybrid BM25 + ANN search over academic papers.
"""
import json
import time
from typing import List, Optional, Dict, Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import Paper

logger = setup_logger(__name__)


class VespaClient:
    """
    Client for Vespa vector search and document store.

    Supports:
    - Document feeding (papers with embeddings)
    - Hybrid search (BM25 + ANN)
    - Semantic-only search (nearest neighbor)
    - Application package deployment
    """

    def __init__(self):
        self.base_url = f"{settings.vespa_host}:{settings.vespa_port}"
        self.deploy_url = f"{settings.vespa_host}:{settings.vespa_deploy_port}"
        self.document_api = f"{self.base_url}/document/v1/default/paper/docid"
        self.search_api = f"{self.base_url}/search/"
        logger.info(f"VespaClient initialized: {self.base_url}")

    def is_healthy(self) -> bool:
        """Check if Vespa is ready to accept requests."""
        try:
            resp = requests.get(
                f"{settings.vespa_host}:{settings.vespa_deploy_port}/state/v1/health",
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def wait_for_ready(self, max_wait: int = 120) -> bool:
        """Wait for Vespa to become ready."""
        logger.info("Waiting for Vespa to be ready...")
        start = time.time()
        while time.time() - start < max_wait:
            if self.is_healthy():
                logger.info("Vespa is ready.")
                return True
            time.sleep(5)
        logger.error(f"Vespa not ready after {max_wait}s")
        return False

    def deploy_application(self, app_package_dir: str = "./vespa") -> bool:
        """
        Deploy the Vespa application package.

        Args:
            app_package_dir: Path to directory containing services.xml and schemas/

        Returns:
            True if deployment was successful
        """
        import zipfile
        import io
        import os

        # Create a zip of the application package
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(app_package_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, app_package_dir)
                    zf.write(fpath, arcname)
        buf.seek(0)

        try:
            resp = requests.post(
                f"{self.deploy_url}/application/v2/tenant/default/prepareandactivate",
                data=buf.read(),
                headers={"Content-Type": "application/zip"},
                timeout=60,
            )
            if resp.status_code in (200, 201):
                logger.info("Vespa application deployed successfully")
                return True
            else:
                logger.error(f"Vespa deploy failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Vespa deploy error: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def index_paper(self, paper: Paper, embedding: List[float]) -> bool:
        """
        Index a single paper with its embedding into Vespa.

        Args:
            paper: Paper model instance
            embedding: Embedding vector (1536-dim for OpenAI)

        Returns:
            True if indexed successfully
        """
        doc = {
            "fields": {
                "paper_id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "published_date": paper.published_date.isoformat(),
                "url": paper.url,
                "source": paper.source,
                "pdf_url": paper.pdf_url or "",
                "citations": paper.citations or 0,
                "embedding": {"values": embedding},
            }
        }

        try:
            resp = requests.post(
                f"{self.document_api}/{paper.id}",
                json=doc,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                logger.debug(f"Indexed paper: {paper.id}")
                return True
            else:
                logger.warning(f"Index failed for {paper.id}: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Index error for {paper.id}: {e}")
            raise

    def index_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> int:
        """
        Batch-index papers with their embeddings.

        Returns:
            Number of successfully indexed papers
        """
        indexed = 0
        for paper, emb in zip(papers, embeddings):
            try:
                if self.index_paper(paper, emb):
                    indexed += 1
            except Exception as e:
                logger.warning(f"Skipping paper {paper.id}: {e}")
        logger.info(f"Indexed {indexed}/{len(papers)} papers into Vespa")
        return indexed

    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
        rank_profile: str = "hybrid",
    ) -> List[Dict[str, Any]]:
        """
        Search Vespa with hybrid BM25 + ANN ranking.

        Args:
            query: Text search query
            query_embedding: Query embedding vector for ANN search
            top_k: Number of results to return
            rank_profile: "hybrid", "semantic", or "default" (BM25 only)

        Returns:
            List of result dictionaries with paper fields and relevance scores
        """
        params: Dict[str, Any] = {
            "yql": f'select * from sources * where userQuery() or ({{targetHits:{top_k}}}nearestNeighbor(embedding, query_embedding))',
            "query": query,
            "hits": top_k,
            "ranking.profile": rank_profile,
        }

        if query_embedding and rank_profile in ("hybrid", "semantic"):
            params["input.query(query_embedding)"] = json.dumps(query_embedding)

        # Fallback to BM25-only if no embedding
        if not query_embedding:
            params["yql"] = "select * from sources * where userQuery()"
            params["ranking.profile"] = "default"

        try:
            resp = requests.get(self.search_api, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for hit in data.get("root", {}).get("children", []):
                fields = hit.get("fields", {})
                fields["_relevance"] = hit.get("relevance", 0.0)
                results.append(fields)

            logger.info(f"Vespa search returned {len(results)} results for: '{query[:50]}...'")
            return results

        except Exception as e:
            logger.error(f"Vespa search failed: {e}")
            return []

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single paper by ID."""
        try:
            resp = requests.get(f"{self.document_api}/{paper_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("fields", {})
            return None
        except Exception as e:
            logger.error(f"Get paper failed for {paper_id}: {e}")
            return None

    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper from the index."""
        try:
            resp = requests.delete(f"{self.document_api}/{paper_id}", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Delete paper failed for {paper_id}: {e}")
            return False
