"""
REST API routes for the Research Assistant.
"""
import json
import asyncio
import concurrent.futures
from typing import List, AsyncGenerator

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
import os
import tempfile

from src.api.schemas import ResearchRequest, ResearchResponse, ReportSummary
from src.agents.orchestrator import ResearchOrchestrator
from src.utils.logger import setup_logger
from src.utils.converter import DocumentConverter
from models.database import get_session, ReportDB, ResearchQueryDB

logger = setup_logger(__name__)

router = APIRouter()

# Thread pool for running research without blocking the event loop
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def run_research_sync(query: str, max_papers: int):
    """Run research synchronously in a thread."""
    orchestrator = ResearchOrchestrator()
    return orchestrator.research(query=query, max_papers=max_papers)


@router.post("/research/stream")
async def execute_research_stream(request: ResearchRequest):
    """
    Execute research with real-time progress streaming via SSE.
    """
    logger.info(f"API: Streaming research request: '{request.query}'")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            orchestrator = ResearchOrchestrator()
            
            # Iterate over real progress events from the orchestrator
            async for event in orchestrator.research_stream(
                query=request.query,
                max_papers=request.max_papers
            ):
                # If we get the final report, handle persistence
                if event["status"] == "complete":
                    report = event["report"]
                    
                    # STRICT PERSISTENCE: Save to DB or Fail
                    try:
                        async for session in get_session():
                            query_record = ResearchQueryDB(
                                query=request.query,
                                papers_fetched=report.papers_analyzed,
                                papers_analyzed=report.papers_analyzed,
                                status="completed",
                            )
                            session.add(query_record)
                            await session.flush()

                            report_record = ReportDB(
                                query_id=query_record.id,
                                query_text=request.query,
                                markdown_content=report.markdown_output,
                                minio_path=report.minio_url,
                                papers_count=report.papers_analyzed,
                                themes=[t.model_dump(mode='json') for t in report.themes],
                                citations=report.citations,
                                top_papers=[p.model_dump(mode='json') for p in report.top_papers],
                            )
                            session.add(report_record)
                            await session.commit()
                            
                            report_id = report_record.id
                            logger.info(f"Report STRICTLY saved to PostgreSQL: {report_id}")
                            break
                            
                    except Exception as db_err:
                        # CRITICAL: If DB fails, tell the user! Do not silently succeed.
                        logger.error(f"DB CONFIGURATION ERROR: {db_err}")
                        yield f"data: {json.dumps({'status': 'error', 'message': 'Database Save Failed! Check Postgres connection.'})}\n\n"
                        return

                    # Only yield complete if DB save worked
                    complete_data = {
                        'status': 'complete',
                        'message': 'Your report is ready!',
                        'report_id': report_id,
                        'query': request.query,
                        'papers_analyzed': report.papers_analyzed,
                        'themes': [t.model_dump(mode='json') for t in report.themes],
                        'citations': report.citations,
                        'markdown_report': report.markdown_output,
                        'top_papers': [p.model_dump(mode='json') for p in report.top_papers],
                        'minio_url': report.minio_url
                    }
                    yield f"data: {json.dumps(complete_data)}\n\n"
                
                elif event["status"] == "error":
                    yield f"data: {json.dumps(event)}\n\n"
                
                else:
                    # Pass through intermediate progress events
                    yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'status': 'error', 'message': f'System Error: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/research", response_model=ResearchResponse)
async def execute_research(request: ResearchRequest):
    """
    Execute a research query through the multi-agent pipeline.

    Returns a structured report with citations and themes.
    """
    logger.info(f"API: Research request received: '{request.query}'")

    try:
        orchestrator = ResearchOrchestrator()
        report = orchestrator.research(
            query=request.query,
            max_papers=request.max_papers,
        )

        # Persist to PostgreSQL
        try:
            async for session in get_session():
                # Save query record
                query_record = ResearchQueryDB(
                    query=request.query,
                    papers_fetched=report.papers_analyzed,
                    papers_analyzed=report.papers_analyzed,
                    status="completed",
                )
                session.add(query_record)
                await session.flush()  # Get the ID

                # Save report record
                report_record = ReportDB(
                    query_id=query_record.id,
                    query_text=request.query,
                    markdown_content=report.markdown_output,
                    minio_path=report.minio_url,
                    papers_count=report.papers_analyzed,
                    themes=[t.model_dump(mode='json') for t in report.themes],
                    citations=report.citations,
                    top_papers=[p.model_dump(mode='json') for p in report.top_papers],
                )
                session.add(report_record)
                await session.commit()

                report.report_id = report_record.id
                logger.info(f"Report saved to PostgreSQL: {report_record.id}")
                break
        except Exception as e:
            logger.error(f"Failed to persist report to DB: {e}")
            raise HTTPException(status_code=500, detail="Database Error: Failed to save report. Please check Postgres connection.")

        return ResearchResponse(
            report_id=report.report_id,
            query=report.query,
            papers_analyzed=report.papers_analyzed,
            themes=[t.model_dump(mode='json') for t in report.themes],
            citations=report.citations,
            markdown_report=report.markdown_output,
            top_papers=[p.model_dump(mode='json') for p in report.top_papers],
            minio_url=report.minio_url,
        )

    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.get("/reports", response_model=List[ReportSummary])
async def list_reports():
    """List all previous research reports."""
    try:
        async for session in get_session():
            from sqlalchemy import select
            result = await session.execute(
                select(ReportDB).order_by(ReportDB.created_at.desc()).limit(50)
            )
            reports = result.scalars().all()
            return [
                ReportSummary(
                    id=r.id,
                    query_text=r.query_text,
                    created_at=r.created_at.isoformat(),
                    papers_count=r.papers_count or 0,
                    themes_count=len(r.themes) if r.themes else 0,
                    citations_count=len(r.citations) if r.citations else 0,
                )
                for r in reports
            ]
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific research report by ID."""
    try:
        async for session in get_session():
            from sqlalchemy import select
            result = await session.execute(
                select(ReportDB).where(ReportDB.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise HTTPException(status_code=404, detail="Report not found")

            return {
                "id": report.id,
                "query_text": report.query_text,
                "created_at": report.created_at.isoformat(),
                "markdown_content": report.markdown_content,
                "minio_path": report.minio_path,
                "papers_count": report.papers_count,
                "themes": report.themes,
                "citations": report.citations,
                "top_papers": report.top_papers,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a research report by ID."""
    try:
        async for session in get_session():
            from sqlalchemy import select
            result = await session.execute(
                select(ReportDB).where(ReportDB.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise HTTPException(status_code=404, detail="Report not found")

            await session.delete(report)
            await session.commit()

            return {"message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete report")


@router.get("/reports/{report_id}/export/{format}")
async def export_report(report_id: str, format: str, background_tasks: BackgroundTasks):
    """
    Export a research report in MD, PDF, or DOCX format.
    """
    format = format.lower()
    if format not in ["md", "pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported: md, pdf, docx")

    try:
        async for session in get_session():
            from sqlalchemy import select
            result = await session.execute(
                select(ReportDB).where(ReportDB.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise HTTPException(status_code=404, detail="Report not found")

            content = report.markdown_content
            title = f"Research Report: {report.query_text}"
            
            # Maryland is standard text
            if format == "md":
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
                temp.write(content.encode("utf-8"))
                temp.close()
                filename = f"research-report-{report_id}.md"
                media_type = "text/markdown"
            
            elif format == "pdf":
                temp_path = os.path.join(tempfile.gettempdir(), f"report-{report_id}.pdf")
                DocumentConverter.to_pdf(content, temp_path, title=title)
                filename = f"research-report-{report_id}.pdf"
                media_type = "application/pdf"
                temp = type('obj', (object,), {'name': temp_path})
                
            elif format == "docx":
                temp_path = os.path.join(tempfile.gettempdir(), f"report-{report_id}.docx")
                DocumentConverter.to_docx(content, temp_path, title=title)
                filename = f"research-report-{report_id}.docx"
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                temp = type('obj', (object,), {'name': temp_path})

            # Schedule file deletion after response
            background_tasks.add_task(os.unlink, temp.name)

            return FileResponse(
                path=temp.name,
                filename=filename,
                media_type=media_type
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for {report_id} in {format}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
