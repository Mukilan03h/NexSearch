"""
Prompt templates for all agents in the research assistant pipeline.
"""

PLANNING_PROMPT = """You are a research planning expert. Given a research query, create a structured search plan.

Research Query: "{query}"

Analyze this query and extract:
1. **keywords**: 3-7 specific search keywords/phrases that will find the most relevant academic papers
2. **max_papers**: How many papers to fetch (10-30, based on query breadth)
3. **time_period**: Relevant time period (e.g., "2023-2025", "last 3 years")
4. **fields**: Academic fields/domains (e.g., "Computer Science", "Machine Learning")
5. **sources**: Which data sources to query (options: "arxiv", "semantic_scholar", "pubmed", "openalex")

Consider:
- Use specific technical terms, not generic ones
- Include both broad and narrow keywords
- For niche topics, use fewer max_papers
- Choose sources appropriate to the field (arxiv for CS/Physics, pubmed for biomedical)

Return a JSON object with these exact fields."""


ANALYSIS_PROMPT = """You are a research analysis expert. Given a set of academic papers and a research query, identify the key themes.

Research Query: "{query}"

Papers:
{papers_text}

Identify 3-5 major themes or topics that emerge across these papers. For each theme:
1. **name**: A concise theme title
2. **description**: A 1-2 sentence description
3. **paper_ids**: List of paper IDs that relate to this theme
4. **relevance_score**: How relevant this theme is to the query (0.0-1.0)

Return a JSON object with a "themes" array containing these theme objects."""


SYNTHESIS_PROMPT = """You are an academic research writer. Synthesize the following papers about a specific theme into a coherent narrative.

Theme: {theme}
Research Query: "{query}"

Papers:
{papers_text}

Write a 2-3 paragraph synthesis that:
- Summarizes the key findings across papers
- Highlights agreements and disagreements between studies
- Notes methodological approaches used
- References papers by their title and authors
- Uses academic writing style

Do NOT use bullet points. Write flowing, connected paragraphs."""


REPORT_PROMPT = """You are a senior research analyst. Generate a comprehensive research report.

Research Query: "{query}"
Number of papers analyzed: {paper_count}

Themes and their synthesized findings:
{themes_content}

Top papers (for citations):
{citations_text}

Generate a complete research report in Markdown format with these sections:

# Research Report: {query}

## Executive Summary
Write 3-4 sentences that:
- Mention the total number of papers and year range
- Describe the main research trend or finding
- Highlight the diversity of applications/approaches
- End with a practical takeaway for researchers

Example: "This review analyzes {paper_count} papers on {query}, published between YYYY and YYYY. The research reveals [main trend], with applications spanning [domain 1], [domain 2], and [domain 3]. Key methodologies include [methods], showing particular strength in [area]. For practitioners, the findings suggest [practical recommendation]."

## Introduction
(2-3 sentences on context, motivation, and scope)

## Key Findings
For each theme (create a subsection), include:
- The theme name as a heading
- 2-3 paragraphs synthesizing findings
- Reference specific papers by title and authors

## Methodology
- Sources searched (e.g., arXiv)
- Number of papers analyzed
- Ranking criteria (relevance score based on embedding similarity)

## Conclusion
- Summary of current state of research
- Emerging trends
- Gaps or contradictions noticed
- Future research directions

## References
(Numbered list: [N] Authors (Year). "Title". Source. URL)

Write in professional academic style. Be specific and cite papers by name."""
