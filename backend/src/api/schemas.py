"""
API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ResearchRequest(BaseModel):
    """POST /research request body."""
    query: str = Field(..., min_length=3, description="Research query")
    max_papers: Optional[int] = Field(None, ge=1, le=50, description="Max papers to fetch")
    output_format: str = Field("markdown", description="Output format")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Recent advances in transformer architectures for NLP",
                "max_papers": 15,
                "output_format": "markdown",
            }
        }


class ResearchResponse(BaseModel):
    """POST /research response body."""
    report_id: Optional[str] = None
    query: str
    papers_analyzed: int
    themes: List[dict] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    markdown_report: str
    top_papers: List[dict] = Field(default_factory=list)
    minio_url: Optional[str] = None


class ReportSummary(BaseModel):
    """GET /reports list item."""
    id: str
    query_text: str
    created_at: str
    papers_count: int
    themes_count: int = 0
    citations_count: int = 0
    themes_count: int = 0
    citations_count: int = 0
