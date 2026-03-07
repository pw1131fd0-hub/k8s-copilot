"""Abstract base class defining the interface for all LLM analyzer implementations."""
from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    """Abstract base class for all LLM analyzer implementations."""

    @abstractmethod
    def analyze(self, prompt: str) -> str:
        """Send prompt to LLM and return raw text response."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of the underlying model."""
