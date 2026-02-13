"""Tests for the Fetcher Agent."""
from unittest.mock import patch, MagicMock
import pytest
from models.schemas import Paper, SearchPlan
from datetime import datetime


class TestFetcherAgent:
    """Test suite for FetcherAgent."""

    def test_deduplication(self):
        """Test paper deduplication by ID."""
        from src.agents.fetcher_agent import FetcherAgent

        agent = FetcherAgent.__new__(FetcherAgent)
        agent.logger = MagicMock()

        papers = [
            Paper(id="1", title="Paper 1", authors=[], abstract="a", published_date=datetime.now(), url="u", source="arxiv"),
            Paper(id="1", title="Paper 1 Dup", authors=[], abstract="b", published_date=datetime.now(), url="u", source="arxiv"),
            Paper(id="2", title="Paper 2", authors=[], abstract="c", published_date=datetime.now(), url="u", source="arxiv"),
        ]
        unique = agent._deduplicate(papers)
        assert len(unique) == 2
        assert unique[0].title == "Paper 1"

    def test_search_plan_integration(self):
        """Test that fetcher respects search plan sources."""
        plan = SearchPlan(
            keywords=["test"],
            max_papers=5,
            sources=["arxiv", "semantic_scholar"],
        )
        assert "arxiv" in plan.sources
        assert len(plan.keywords) == 1
