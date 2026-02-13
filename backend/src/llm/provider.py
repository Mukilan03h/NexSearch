"""
LLM provider abstraction using LiteLLM for multi-provider support.
Supports OpenAI, Anthropic, Ollama, Azure, and more through a single interface.
"""
import json
from typing import Type, Optional, List

import litellm
from pydantic import BaseModel

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Suppress LiteLLM verbose logging
litellm.suppress_debug_info = True


class LLMProvider:
    """
    Unified LLM interface powered by LiteLLM.

    Supports automatic routing to OpenAI, Anthropic, Ollama, etc.
    based on the configured provider and model.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the LLM provider.

        Args:
            model: Override model name (e.g., 'gpt-4-turbo-preview', 'ollama/llama3.2')
        """
        self.model = model or settings.litellm_model
        self.api_base = settings.litellm_api_base

        # Set API keys for LiteLLM
        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key
        if settings.groq_api_key:
            litellm.groq_key = settings.groq_api_key
        if settings.groq_api_key:
            litellm.groq_key = settings.groq_api_key

        logger.info(f"LLMProvider initialized: model={self.model}, api_base={self.api_base}")

    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate a text completion.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (0.0=deterministic, 1.0=creative)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system-level instruction
            timeout: Request timeout in seconds (default from settings)

        Returns:
            Generated text string
        """
        timeout = timeout or settings.llm_timeout

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=self.api_base,
                timeout=timeout,
                **kwargs,
            )
            content = response.choices[0].message.content
            logger.debug(f"LLM completion: {len(content)} chars, model={self.model}")
            return content

        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise

    def complete_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.0,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> BaseModel:
        """
        Generate structured output matching a Pydantic schema (JSON mode).

        Args:
            prompt: User prompt
            schema: Pydantic model class for output structure
            temperature: Usually 0.0 for reliable structured output
            timeout: Request timeout in seconds (default from settings)

        Returns:
            Validated instance of the schema class
        """
        timeout = timeout or settings.llm_timeout
        schema_json = schema.model_json_schema()
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"Return ONLY valid JSON matching this schema (no markdown, no explanation):\n"
            f"{json.dumps(schema_json, indent=2)}"
        )

        messages = [
            {"role": "system", "content": "You are a precise JSON generator. Output only valid JSON."},
            {"role": "user", "content": enhanced_prompt},
        ]

        try:
            # Try JSON mode if provider supports it
            extra_kwargs = {}
            if not settings.enable_ollama and "ollama" not in self.model:
                extra_kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.max_tokens,
                api_base=self.api_base,
                timeout=timeout,
                **extra_kwargs,
                **kwargs,
            )

            content = response.choices[0].message.content

            # Strip markdown fences if present
            if content.strip().startswith("```"):
                lines = content.strip().split("\n")
                content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

            return schema.model_validate_json(content)

        except Exception as e:
            logger.error(f"Structured completion failed: {e}")
            raise
