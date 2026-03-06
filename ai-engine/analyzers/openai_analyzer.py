import os
from openai import OpenAI
from ai_engine.analyzers.base_analyzer import BaseAnalyzer


class OpenAIAnalyzer(BaseAnalyzer):
    """Analyzer using OpenAI's GPT models (cloud, requires API key)."""

    def __init__(self):
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o")

    @property
    def model_name(self) -> str:
        return f"openai/{self._model}"

    def analyze(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500,
        )
        return response.choices[0].message.content or ""
