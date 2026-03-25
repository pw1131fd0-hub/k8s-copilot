"""AI analyzer backed by OpenAI's GPT models."""
import os
from openai import OpenAI
from ai_engine.analyzers.base_analyzer import BaseAnalyzer


class OpenAIAnalyzer(BaseAnalyzer):
    """Analyzer using OpenAI's GPT models (cloud, requires API key)."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is not set or is empty")
        self._client = OpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o")

    @property
    def model_name(self) -> str:
        """Return the fully-qualified OpenAI model identifier."""
        return f"openai/{self._model}"

    def analyze(self, prompt: str) -> str:
        """Send prompt to OpenAI chat completions API and return the response text."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc
