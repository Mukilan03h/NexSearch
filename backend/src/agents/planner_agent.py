"""
Planning Agent — analyzes research queries and generates structured search plans.
Uses LLM structured output to extract keywords, time periods, and data sources.
"""
from src.agents.base_agent import BaseAgent
from src.llm.prompts import PLANNING_PROMPT
from src.utils.config import settings
from models.schemas import SearchPlan


class PlannerAgent(BaseAgent):
    """
    Analyzes a natural language research query and produces a SearchPlan.

    The SearchPlan includes optimized keywords, time period, academic fields,
    and which data sources to query.
    """

    def execute(self, query: str) -> SearchPlan:
        """Alias for create_search_plan."""
        return self.create_search_plan(query)

    def create_search_plan(self, query: str) -> SearchPlan:
        """
        Generate a structured search plan from a research query.

        Args:
            query: Natural language research query (e.g., "Recent advances in transformers")

        Returns:
            SearchPlan with extracted keywords, sources, and parameters
        """
        self.logger.info(f"Creating search plan for: '{query}'")

        prompt = PLANNING_PROMPT.format(query=query)

        try:
            plan = self.llm.complete_structured(
                prompt=prompt,
                schema=SearchPlan,
                temperature=settings.temperature_planning,
            )

            # Ensure arXiv is always included as primary source
            if "arxiv" not in plan.sources:
                plan.sources.insert(0, "arxiv")

            # Cap max papers to configured limit
            plan.max_papers = min(plan.max_papers, settings.max_papers_per_query * 2)

            self.logger.info(
                f"Search plan created: {len(plan.keywords)} keywords, "
                f"{plan.max_papers} max papers, sources={plan.sources}"
            )
            return plan

        except Exception as e:
            self.logger.error(f"Search plan creation failed: {e}")
            # Fallback: create a basic plan from the query
            self.logger.warning("Using fallback search plan")
            return SearchPlan(
                keywords=query.split()[:5],
                max_papers=settings.max_papers_per_query,
                time_period="last 2 years",
                fields=["Computer Science"],
                sources=["arxiv"],
            )
