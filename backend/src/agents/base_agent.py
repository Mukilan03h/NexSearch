"""
Abstract base class for all agents in the research assistant pipeline.
"""
from abc import ABC, abstractmethod
from typing import Any

from src.llm.provider import LLMProvider
from src.utils.logger import setup_logger


class BaseAgent(ABC):
    """
    Base class for all specialized agents.

    Provides:
    - LLM provider access
    - Structured logging
    - Common execute() contract
    """

    def __init__(self, llm: LLMProvider = None):
        """
        Initialize agent with an LLM provider.

        Args:
            llm: LLMProvider instance (creates default if not provided)
        """
        self.llm = llm or LLMProvider()
        self.logger = setup_logger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the agent's primary task."""
        ...
