"""AI analyzer backed by Google's Gemini generative models."""
import os
from google import genai
from google.genai import types
from ai_engine.analyzers.base_analyzer import BaseAnalyzer


class GeminiAnalyzer(BaseAnalyzer):
    """Analyzer using Google's Gemini models (cloud, requires API key)."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set or is empty")
        self._client = genai.Client(api_key=api_key)
        self._model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    @property
    def model_name(self) -> str:
        """Return the fully-qualified Gemini model identifier."""
        return f"gemini/{self._model_id}"

    def analyze(self, prompt: str) -> str:
        """Send prompt to the Gemini generative model and return the response text."""
        try:
            response = self._client.models.generate_content(
                model=self._model_id,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=1500),
            )
            return response.text or ""
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc
