"""Tests for the Analyzer Agent."""
from unittest.mock import patch, MagicMock

import pytest
from models.schemas import Paper, Theme
from datetime import datetime


class TestAnalyzerAgent:
    """Test suite for AnalyzerAgent."""

    def test_cosine_similarity_ranking(self):
        """Test the cosine similarity fallback ranking."""
        from src.agents.analyzer_agent import AnalyzerAgent

        agent = AnalyzerAgent.__new__(AnalyzerAgent)
        agent.logger = MagicMock()

        papers = [
            Paper(id=f"p{i}", title=f"Paper {i}", authors=[], abstract="test",
                  published_date=datetime.now(), url="u", source="arxiv")
            for i in range(5)
        ]

        # Simple embeddings for testing
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.0],
        ]
        query_emb = [1.0, 0.0, 0.0]

        ranked = agent._cosine_rank(papers, embeddings, query_emb, top_k=3)
        assert len(ranked) == 3
        # First paper should be most similar to query
        assert ranked[0].id == "p0"
        assert ranked[1].id == "p1"

    def test_theme_model(self):
        """Test Theme model creation."""
        theme = Theme(
            name="Test Theme",
            description="A test theme",
            paper_ids=["p1", "p2"],
            relevance_score=0.85,
        )
        assert theme.name == "Test Theme"
        assert len(theme.paper_ids) == 2
