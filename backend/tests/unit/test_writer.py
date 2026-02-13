"""Tests for the Writer Agent."""
from unittest.mock import patch, MagicMock

import pytest
from models.schemas import Paper, Theme, ResearchReport
from datetime import datetime


class TestWriterAgent:
    """Test suite for WriterAgent."""

    def test_citation_formatting(self):
        """Test academic citation formatting."""
        from src.agents.writer_agent import WriterAgent

        agent = WriterAgent.__new__(WriterAgent)
        agent.logger = MagicMock()

        papers = [
            Paper(
                id="p1", title="Test Paper Title",
                authors=["Alice Smith", "Bob Jones", "Carol White", "Dave Brown"],
                abstract="test", published_date=datetime(2023, 6, 15),
                url="https://arxiv.org/abs/p1", source="arxiv",
            )
        ]

        citations = agent._format_citations(papers)
        assert len(citations) == 1
        assert "Alice Smith" in citations[0]
        assert "et al." in citations[0]
        assert "2023" in citations[0]
        assert "Test Paper Title" in citations[0]

    def test_empty_report(self):
        """Test empty report generation when no papers found."""
        from src.agents.writer_agent import WriterAgent

        agent = WriterAgent.__new__(WriterAgent)
        agent.logger = MagicMock()

        report = agent._empty_report("test query")
        assert isinstance(report, ResearchReport)
        assert report.papers_analyzed == 0
        assert "No relevant papers" in report.markdown_output

    def test_report_model(self):
        """Test ResearchReport model."""
        report = ResearchReport(
            query="test",
            papers_analyzed=5,
            markdown_output="# Report\nContent",
            citations=["[1] Test citation"],
        )
        assert report.papers_analyzed == 5
        assert len(report.citations) == 1
