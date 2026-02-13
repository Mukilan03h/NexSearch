"""Tests for the Planner Agent."""
from unittest.mock import patch, MagicMock

import pytest
from models.schemas import SearchPlan


class TestPlannerAgent:
    """Test suite for PlannerAgent."""

    def test_search_plan_model(self):
        """Test SearchPlan model validation."""
        plan = SearchPlan(
            keywords=["transformer", "NLP"],
            max_papers=10,
            time_period="2023-2025",
            fields=["CS"],
            sources=["arxiv"],
        )
        assert len(plan.keywords) == 2
        assert plan.max_papers == 10
        assert "arxiv" in plan.sources

    def test_search_plan_defaults(self):
        """Test SearchPlan default values."""
        plan = SearchPlan(keywords=["test"])
        assert plan.max_papers == 20
        assert plan.sources == ["arxiv"]

    @patch("src.agents.planner_agent.PlannerAgent.__init__", return_value=None)
    def test_fallback_plan(self, mock_init):
        """Test that planner produces a fallback plan on LLM failure."""
        from src.agents.planner_agent import PlannerAgent

        agent = PlannerAgent.__new__(PlannerAgent)
        agent.llm = MagicMock()
        agent.logger = MagicMock()

        # Simulate LLM failure
        agent.llm.complete_structured.side_effect = Exception("LLM unavailable")

        plan = agent.create_search_plan("test query about AI")
        assert isinstance(plan, SearchPlan)
        assert len(plan.keywords) > 0
        assert "arxiv" in plan.sources
