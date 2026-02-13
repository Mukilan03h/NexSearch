"""
Orchestrator — coordinates all agents in the research pipeline.
Manages the Plan → Fetch → Analyze → Write workflow with timing and persistence.
"""
import uuid
from datetime import datetime
from typing import Optional, Callable

from src.agents.base_agent import BaseAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.fetcher_agent import FetcherAgent
from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.writer_agent import WriterAgent
from src.storage.minio_client import MinIOClient
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.schemas import ResearchReport

logger = setup_logger(__name__)


class ProgressCallback:
    """Container for progress callback function."""

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback

    def emit(self, stage: str, message: str, progress: int):
        """Emit a progress update if a callback is registered."""
        if self.callback:
            self.callback(stage, message, progress)


class ResearchOrchestrator:
    """
    Coordinates the multi-agent research workflow:

    1. **PlannerAgent** → Analyze query, generate search plan
    2. **FetcherAgent** → Fetch papers from enabled sources
    3. **AnalyzerAgent** → Rank papers, extract themes
    4. **WriterAgent** → Generate structured research report
    """

    def __init__(self):
        logger.info("Initializing Research Orchestrator...")

        self.planner = PlannerAgent()
        self.fetcher = FetcherAgent()
        self.analyzer = AnalyzerAgent()
        self.writer = WriterAgent()
        self.minio: Optional[MinIOClient] = None

        logger.info("All agents initialized successfully")

    def _get_minio(self) -> Optional[MinIOClient]:
        """Lazy-init MinIO client."""
        if self.minio is None:
            try:
                self.minio = MinIOClient()
                self.minio.ensure_buckets()
            except Exception as e:
                logger.warning(f"MinIO not available for report storage: {e}")
        return self.minio

    async def research_stream(
        self,
        query: str,
        max_papers: Optional[int] = None,
    ):
        """
        Execute the full research workflow as an async generator.
        Yields progress events -> final ResearchReport.
        """
        report_id = str(uuid.uuid4())[:8]
        logger.info(f"[{report_id}] Starting research stream: '{query}'")
        start_time = datetime.now()

        yield {"status": "starting", "message": f"Initializing research for: {query}..."}

        try:
            # Step 1: Planning
            logger.info(f"[{report_id}] STEP 1/4: Creating search plan...")
            yield {"status": "planning", "message": "Creating search plan..."}
            
            # Run blocking LLM call in thread
            plan = await self._run_in_executor(self.planner.create_search_plan, query)
            
            if max_papers:
                plan.max_papers = max_papers
            
            yield {"status": "planned", "message": f"Plan: {len(plan.keywords)} keywords, sources={plan.sources}"}

            # Step 2: Fetching
            logger.info(f"[{report_id}] STEP 2/4: Fetching papers...")
            yield {"status": "fetching", "message": f"Searching for papers max={plan.max_papers}..."}
            
            papers = await self._run_in_executor(self.fetcher.fetch_papers, plan)
            total_papers = len(papers)
            
            if not papers:
                logger.warning(f"[{report_id}] No papers found")
                yield {"status": "error", "message": "No papers found matching the criteria."}
                return

            yield {"status": "fetched", "message": f"Fetched {total_papers} unique papers", "papers_count": total_papers}

            # Step 3: Analysis
            logger.info(f"[{report_id}] STEP 3/4: Analyzing and ranking...")
            yield {"status": "analyzing", "message": f"Analyzing {total_papers} papers & extracting themes..."}
            
            # Run analysis in thread (CPU heavy)
            top_papers = await self._run_in_executor(
                self.analyzer.rank_and_filter, papers, query, settings.top_k_papers
            )
            themes = await self._run_in_executor(
                self.analyzer.extract_themes, top_papers, query
            )
            
            yield {"status": "analyzed", "message": f"Identified {len(themes)} key themes from {len(top_papers)} top papers."}

            # Step 4: Writing
            logger.info(f"[{report_id}] STEP 4/4: Generating report...")
            yield {"status": "writing", "message": "Synthesizing final research report..."}
            
            report = await self._run_in_executor(
                self.writer.generate_report, query, top_papers, themes
            )
            report.report_id = report_id

            # Store in MinIO (Async-friendly check)
            minio = self._get_minio()
            if minio:
                try:
                    # MinIO upload might be blocking, run in executor
                    minio_path = await self._run_in_executor(
                        minio.upload_report, report_id, report.markdown_output
                    )
                    report.minio_url = minio_path
                except Exception as e:
                    logger.error(f"MinIO upload failed: {e}") 
                    # We don't fail the whole request for MinIO, but we log it.

            # Final Yield - The complete data
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{report_id}] Finished in {elapsed:.1f}s")
            
            yield {
                "status": "complete",
                "message": "Research complete!",
                "report": report
            }

        except Exception as e:
            logger.error(f"[{report_id}] Stream failed: {e}", exc_info=True)
            yield {"status": "error", "message": f"Research failed: {str(e)}"}
            raise e

    async def _run_in_executor(self, func, *args):
        """Run blocking sync functions in a thread pool."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
