"""AI analyzer backed by a locally running Ollama instance."""
import os
import httpx
from ai_engine.analyzers.base_analyzer import BaseAnalyzer


class OllamaAnalyzer(BaseAnalyzer):
    """Analyzer using a locally running Ollama instance (local-first, privacy-safe)."""

    def __init__(self) -> None:
        self._base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = os.getenv("OLLAMA_MODEL", "llama3")

    @property
    def model_name(self) -> str:
        """Return the fully-qualified Ollama model identifier."""
        return f"ollama/{self._model}"

    def is_available(self) -> bool:
        """Return True if the Ollama service responds within 3 seconds."""
        try:
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def analyze(self, prompt: str) -> str:
        """Send prompt to the Ollama generate API and return the response text."""
        try:
            response = httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
