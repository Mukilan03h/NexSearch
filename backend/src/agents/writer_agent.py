"""
Writer Agent — synthesizes analyzed papers into a structured research report.
Generates markdown reports with executive summary, findings, and citations.
"""
from typing import List

from src.agents.base_agent import BaseAgent
from src.llm.prompts import SYNTHESIS_PROMPT, REPORT_PROMPT
from src.utils.config import settings
from models.schemas import Paper, Theme, ResearchReport


class WriterAgent(BaseAgent):
    """
    Generates comprehensive research reports by:
    1. Synthesizing findings for each theme
    2. Generating a structured markdown report
    3. Formatting proper academic citations
    """

    def execute(self, query: str, papers: List[Paper], themes: List[Theme] = None) -> ResearchReport:
        """Alias for generate_report."""
        return self.generate_report(query, papers, themes)

    def generate_report(
        self, query: str, papers: List[Paper], themes: List[Theme] = None
    ) -> ResearchReport:
        """
        Generate a complete research report.

        Args:
            query: Original research query
            papers: Analyzed and ranked papers
            themes: Extracted themes (optional, generated if not provided)

        Returns:
            ResearchReport with markdown content and metadata
        """
        self.logger.info(f"Generating report for: '{query}' ({len(papers)} papers)")

        if not papers:
            return self._empty_report(query)

        # Build citation list
        citations = self._format_citations(papers)
        citations_text = "\n".join(citations)

        # Synthesize content per theme
        themes_content = ""
        if themes:
            for theme in themes:
                theme_papers = [p for p in papers if p.id in theme.paper_ids]
                if not theme_papers:
                    theme_papers = papers[:3]
                synthesis = self._synthesize_theme(query, theme, theme_papers)
                themes_content += f"\n### {theme.name}\n{synthesis}\n"
        else:
            # No themes provided — synthesize all papers together
            themes_content = self._synthesize_all(query, papers)

        # Generate full report
        prompt = REPORT_PROMPT.format(
            query=query,
            paper_count=len(papers),
            themes_content=themes_content,
            citations_text=citations_text,
        )

        try:
            markdown = self.llm.complete(
                prompt=prompt,
                temperature=settings.temperature_writing,
                max_tokens=settings.max_tokens,
            )
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            markdown = self._fallback_report(query, papers, citations)

        report = ResearchReport(
            query=query,
            papers_analyzed=len(papers),
            markdown_output=markdown,
            citations=citations,
            themes=themes or [],
            top_papers=papers[:5],
        )

        self.logger.info(f"Report generated: {len(markdown)} chars, {len(citations)} citations")
        return report

    def _synthesize_theme(self, query: str, theme: Theme, papers: List[Paper]) -> str:
        """Synthesize papers for a specific theme."""
        papers_text = self._format_papers_for_prompt(papers)
        prompt = SYNTHESIS_PROMPT.format(
            theme=f"{theme.name}: {theme.description}",
            query=query,
            papers_text=papers_text,
        )
        try:
            return self.llm.complete(prompt=prompt, temperature=0.6, max_tokens=1000)
        except Exception as e:
            self.logger.warning(f"Theme synthesis failed: {e}")
            return f"Key papers on {theme.name}: " + ", ".join(
                [f'"{p.title}"' for p in papers[:3]]
            )

    def _synthesize_all(self, query: str, papers: List[Paper]) -> str:
        """Synthesize all papers when no themes are available."""
        papers_text = self._format_papers_for_prompt(papers)
        prompt = SYNTHESIS_PROMPT.format(
            theme="General Findings",
            query=query,
            papers_text=papers_text,
        )
        try:
            return self.llm.complete(prompt=prompt, temperature=0.6, max_tokens=1500)
        except Exception as e:
            self.logger.warning(f"Synthesis failed: {e}")
            return "\n".join([f"- **{p.title}** ({p.source}): {p.abstract[:150]}..." for p in papers])

    def _format_papers_for_prompt(self, papers: List[Paper]) -> str:
        """Format papers for inclusion in LLM prompts."""
        return "\n\n".join([
            f"**[{i+1}] {p.title}**\n"
            f"Authors: {', '.join(p.authors[:5])}\n"
            f"Source: {p.source} | Published: {p.published_date.strftime('%Y-%m-%d')}\n"
            f"Relevance Score: {p.relevance_score:.2%}\n"
            f"Abstract: {self._truncate_abstract(p.abstract)}"
            for i, p in enumerate(papers)
        ])

    def _truncate_abstract(self, abstract: str, max_words: int = 200) -> str:
        """Truncate abstract to word limit, preferring complete sentences."""
        words = abstract.split()
        if len(words) <= max_words:
            return abstract
        # Find the last sentence boundary within the limit
        truncated = " ".join(words[:max_words])
        # Try to end at a sentence boundary
        for punct in ['. ', '? ', '! ']:
            last_punct = truncated.rfind(punct)
            if last_punct > max_words * 0.7:  # At least 70% of limit
                return truncated[:last_punct + 1]
        return truncated + "..."

    def _format_citations(self, papers: List[Paper]) -> List[str]:
        """Format papers as academic citations."""
        citations = []
        for i, p in enumerate(papers, 1):
            authors_str = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors_str += " et al."
            year = p.published_date.strftime("%Y")
            citation = f'[{i}] {authors_str} ({year}). "{p.title}". {p.source.replace("_", " ").title()}. {p.url}'
            citations.append(citation)
        return citations

    def _empty_report(self, query: str) -> ResearchReport:
        """Return a report indicating no papers were found."""
        markdown = (
            f"# Research Report: {query}\n\n"
            f"## Summary\n\n"
            f"No relevant papers were found for this query. "
            f"Please try broadening your search terms or checking different data sources.\n"
        )
        return ResearchReport(
            query=query,
            papers_analyzed=0,
            markdown_output=markdown,
            citations=[],
        )

    def _fallback_report(self, query: str, papers: List[Paper], citations: List[str]) -> str:
        """Generate a basic report without LLM when it fails."""
        sections = [f"# Research Report: {query}\n"]

        # Generate summary based on papers
        papers_by_year = {}
        for p in papers:
            year = p.published_date.strftime("%Y")
            papers_by_year.setdefault(year, []).append(p)

        sections.append(f"## Summary\nAnalyzed {len(papers)} papers from {min(papers_by_year.keys())} to {max(papers_by_year.keys())}.\n")

        sections.append("## Papers Found\n")
        for p in papers:
            sections.append(f"### {p.title}\n- **Authors**: {', '.join(p.authors[:3])}")
            sections.append(f"- **Relevance**: {p.relevance_score:.1%}")
            sections.append(f"- **Abstract**: {self._truncate_abstract(p.abstract, 150)}\n")
        sections.append("## References\n" + "\n".join(citations))
        return "\n".join(sections)
