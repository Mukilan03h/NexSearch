"""
Shared test fixtures for unit and integration tests.
"""
import pytest
from datetime import datetime
from models.schemas import Paper, SearchPlan, Theme


@pytest.fixture
def sample_paper():
    """Create a sample Paper for testing."""
    return Paper(
        id="2301.00001",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        published_date=datetime(2023, 1, 1),
        url="https://arxiv.org/abs/2301.00001",
        source="arxiv",
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
    )


@pytest.fixture
def sample_papers():
    """Create a list of sample Papers for testing."""
    return [
        Paper(
            id=f"2301.0000{i}",
            title=f"Paper Title {i}: {topic}",
            authors=[f"Author {i}"],
            abstract=f"This paper studies {topic} using novel methods...",
            published_date=datetime(2023, i, 1),
            url=f"https://arxiv.org/abs/2301.0000{i}",
            source="arxiv",
        )
        for i, topic in enumerate([
            "transformers", "attention mechanisms", "BERT",
            "GPT architecture", "language modeling"
        ], 1)
    ]


@pytest.fixture
def sample_search_plan():
    """Create a sample SearchPlan for testing."""
    return SearchPlan(
        keywords=["transformer", "attention", "NLP"],
        max_papers=10,
        time_period="2023-2025",
        fields=["Computer Science", "AI"],
        sources=["arxiv"],
    )


@pytest.fixture
def sample_themes():
    """Create sample Themes for testing."""
    return [
        Theme(
            name="Transformer Architectures",
            description="Novel modifications to the transformer architecture",
            paper_ids=["2301.00001", "2301.00002"],
            relevance_score=0.9,
        ),
        Theme(
            name="Attention Mechanisms",
            description="New forms of attention beyond standard self-attention",
            paper_ids=["2301.00002", "2301.00003"],
            relevance_score=0.85,
        ),
    ]
