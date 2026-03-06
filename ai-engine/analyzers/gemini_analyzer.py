import os
import google.generativeai as genai
from ai_engine.analyzers.base_analyzer import BaseAnalyzer


class GeminiAnalyzer(BaseAnalyzer):
    """Analyzer using Google's Gemini models (cloud, requires API key)."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        genai.configure(api_key=api_key)
        self._model_id = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self._model = genai.GenerativeModel(self._model_id)

    @property
    def model_name(self) -> str:
        return f"gemini/{self._model_id}"

    def analyze(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text or ""
