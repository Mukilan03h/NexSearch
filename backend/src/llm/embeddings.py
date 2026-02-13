"""
Embedding generation using LiteLLM for multi-provider support.
"""
from typing import List, Optional

import litellm
import requests

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingProvider:
    """Generate embeddings for semantic search using LiteLLM."""

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize embedding provider.

        Args:
            model: Override embedding model (default from settings)
            provider: Override provider - "openai", "ollama", "anthropic"
        """
        self.provider = provider or settings.embedding_provider
        self.model = model or settings.embedding_model

        if settings.openai_api_key and self.provider != "ollama":
            litellm.openai_key = settings.openai_api_key

        logger.info(f"EmbeddingProvider initialized: model={self.model}, provider={self.provider}")

    def generate(self, texts: List[str], timeout: Optional[int] = None) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed
            timeout: Request timeout in seconds (default from settings)

        Returns:
            List of embedding vectors (each a list of floats)
        """
        if not texts:
            return []

        timeout = timeout or settings.embedding_timeout
        all_embeddings = []

        # Use direct HTTP for Ollama to avoid LiteLLM endpoint issues
        if self.provider == "ollama":
            for text in texts:
                try:
                    response = requests.post(
                        f"{settings.ollama_host}/api/embeddings",
                        json={"model": self.model, "prompt": text},
                        timeout=timeout,
                    )
                    response.raise_for_status()
                    all_embeddings.append(response.json()["embedding"])
                except Exception as e:
                    logger.error(f"Ollama embedding generation failed: {e}")
                    raise

            logger.debug(f"Generated {len(all_embeddings)} embeddings via Ollama")
            return all_embeddings

        # Use LiteLLM for OpenAI and other providers
        batch_size = 100  # OpenAI batch limit
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                response = litellm.embedding(
                    model=self.model,
                    input=batch,
                    timeout=timeout,
                )
                batch_embeddings = [item["embedding"] for item in response.data]
                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"Embedding generation failed for batch {i}: {e}")
                raise

        logger.debug(f"Generated {len(all_embeddings)} embeddings (dim={len(all_embeddings[0]) if all_embeddings else 0})")
        return all_embeddings

    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        return self.generate([text])[0]
