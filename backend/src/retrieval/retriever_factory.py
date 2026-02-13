"""
Factory for creating retriever instances based on configuration.
Enables dynamic provider selection at runtime.
"""
from typing import List

from src.retrieval.base_retriever import BaseRetriever
from src.retrieval.arxiv_client import ArxivClient
from src.retrieval.semantic_scholar import SemanticScholarClient
from src.retrieval.pubmed_client import PubMedClient
from src.retrieval.openalex_client import OpenAlexClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Registry of all available retrievers
_RETRIEVER_CLASSES = [
    ArxivClient,
    SemanticScholarClient,
    PubMedClient,
    OpenAlexClient,
]


def get_retrievers() -> List[BaseRetriever]:
    """
    Get all enabled retriever instances.

    Returns:
        List of retriever instances that are available and configured
    """
    retrievers = []
    for cls in _RETRIEVER_CLASSES:
        instance = cls()
        if instance.is_available():
            retrievers.append(instance)
            logger.info(f"Retriever enabled: {instance.source_name}")
        else:
            logger.debug(f"Retriever disabled: {instance.source_name}")

    if not retrievers:
        logger.warning("No retrievers enabled! Falling back to arXiv only.")
        retrievers = [ArxivClient()]

    return retrievers


def get_retriever_by_name(name: str) -> BaseRetriever:
    """Get a specific retriever by source name."""
    mapping = {
        "arxiv": ArxivClient,
        "semantic_scholar": SemanticScholarClient,
        "pubmed": PubMedClient,
        "openalex": OpenAlexClient,
    }
    cls = mapping.get(name)
    if cls is None:
        raise ValueError(f"Unknown retriever: {name}. Available: {list(mapping.keys())}")
    return cls()
