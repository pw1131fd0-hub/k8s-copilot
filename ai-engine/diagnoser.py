import os
import json
import logging
import re
from ai_engine.prompts.k8s_prompts import DIAGNOSE_PROMPT_TEMPLATE
from ai_engine.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class AIDiagnoser:
    """
    AI diagnosis engine with local-first routing strategy:
    1. Tries Ollama (local) first if available.
    2. Falls back to OpenAI or Gemini (cloud) if local is unavailable.
    """

    def __init__(self) -> None:
        self._analyzer: BaseAnalyzer | None = None

    def _get_analyzer(self) -> BaseAnalyzer:
        if self._analyzer:
            return self._analyzer

        # Local-first: try Ollama
        if os.getenv("OLLAMA_BASE_URL") or os.path.exists("/tmp/ollama_available"):
            from ai_engine.analyzers.ollama_analyzer import OllamaAnalyzer
            ollama = OllamaAnalyzer()
            if ollama.is_available():
                self._analyzer = ollama
                return self._analyzer

        # Cloud fallback: OpenAI
        if os.getenv("OPENAI_API_KEY"):
            from ai_engine.analyzers.openai_analyzer import OpenAIAnalyzer
            self._analyzer = OpenAIAnalyzer()
            return self._analyzer

        # Cloud fallback: Gemini
        if os.getenv("GEMINI_API_KEY"):
            from ai_engine.analyzers.gemini_analyzer import GeminiAnalyzer
            self._analyzer = GeminiAnalyzer()
            return self._analyzer

        raise RuntimeError(
            "No AI provider available. Set OPENAI_API_KEY, GEMINI_API_KEY, or start Ollama locally."
        )

    def suggest(self, prompt: str) -> str:
        """Send a raw prompt to the configured AI provider and return the response text."""
        try:
            analyzer = self._get_analyzer()
            return analyzer.analyze(prompt)
        except RuntimeError:
            return ""
        except Exception:
            logger.exception("Unexpected error during AI suggestion")
            return ""

    def diagnose(self, context: dict) -> dict:
        """
        Run AI diagnosis on a pod context dict.
        Expected context keys: pod_name, namespace, error_type, describe, logs
        Returns: dict with root_cause, remediation, raw_analysis, model_used
        """
        prompt = DIAGNOSE_PROMPT_TEMPLATE.format(
            pod_name=context.get("pod_name", "unknown"),
            namespace=context.get("namespace", "default"),
            error_type=context.get("error_type", "Unknown"),
            describe=context.get("describe", "N/A"),
            logs=context.get("logs", "N/A"),
        )

        try:
            analyzer = self._get_analyzer()
            raw_response = analyzer.analyze(prompt)
            model_used = analyzer.model_name

            parsed = self._parse_response(raw_response)
            parsed["raw_analysis"] = raw_response
            parsed["model_used"] = model_used
            return parsed

        except RuntimeError as e:
            # No LLM provider configured - return structured stub
            return {
                "root_cause": f"AI provider not configured: {e}",
                "remediation": "Please configure OPENAI_API_KEY, GEMINI_API_KEY, or start Ollama locally.",
                "raw_analysis": str(e),
                "model_used": "none",
            }
        except Exception as e:
            logger.exception("Unexpected error during AI diagnosis for pod '%s'", context.get("pod_name"))
            return {
                "root_cause": f"Diagnosis failed: {e}",
                "remediation": "Check AI provider connectivity and retry.",
                "raw_analysis": str(e),
                "model_used": "error",
            }

    def _parse_response(self, raw: str) -> dict:
        """Extract structured fields from LLM JSON response."""
        # Use greedy matching to capture complete nested JSON objects
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)

        try:
            data = json.loads(raw)
            return {
                "root_cause": data.get("root_cause", ""),
                "detailed_analysis": data.get("detailed_analysis") or None,
                "remediation": data.get("remediation", ""),
            }
        except json.JSONDecodeError:
            # Graceful degradation: return raw text as root_cause
            return {
                "root_cause": raw[:500] if raw else "No analysis available",
                "detailed_analysis": None,
                "remediation": "Review the raw analysis above for remediation steps.",
            }


if __name__ == '__main__':
    engine = AIDiagnoser()
    result = engine.diagnose({
        "pod_name": "test-pod",
        "namespace": "default",
        "error_type": "CrashLoopBackOff",
        "describe": "Phase: Failed",
        "logs": "Error: cannot connect to database",
    })
    print(result)
