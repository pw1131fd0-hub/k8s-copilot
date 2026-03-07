"""Multi-model AI diagnosis engine with local-first (Ollama → OpenAI → Gemini) routing."""
import os
import json
import logging
import re
from typing import TypedDict
from ai_engine.prompts.k8s_prompts import DIAGNOSE_PROMPT_TEMPLATE
from ai_engine.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class ParsedResponse(TypedDict):
    """Structured fields extracted from an LLM JSON response."""

    root_cause: str
    detailed_analysis: str | None
    remediation: str


class DiagnoseResult(ParsedResponse):
    """Full AI diagnosis result including raw LLM output and model identifier."""

    raw_analysis: str
    model_used: str


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
            from ai_engine.analyzers.ollama_analyzer import OllamaAnalyzer  # pylint: disable=import-outside-toplevel
            ollama = OllamaAnalyzer()
            if ollama.is_available():
                self._analyzer = ollama
                return self._analyzer

        # Cloud fallback: OpenAI
        if os.getenv("OPENAI_API_KEY"):
            from ai_engine.analyzers.openai_analyzer import OpenAIAnalyzer  # pylint: disable=import-outside-toplevel
            self._analyzer = OpenAIAnalyzer()
            return self._analyzer

        # Cloud fallback: Gemini
        if os.getenv("GEMINI_API_KEY"):
            from ai_engine.analyzers.gemini_analyzer import GeminiAnalyzer  # pylint: disable=import-outside-toplevel
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
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Unexpected error during AI suggestion")
            return ""

    def diagnose(self, context: dict) -> DiagnoseResult:
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
            return DiagnoseResult(
                root_cause=parsed["root_cause"],
                detailed_analysis=parsed["detailed_analysis"],
                remediation=parsed["remediation"],
                raw_analysis=raw_response,
                model_used=model_used,
            )

        except RuntimeError as e:
            # No LLM provider configured - return structured stub
            return DiagnoseResult(
                root_cause=f"AI provider not configured: {e}",
                remediation=(
                    "Please configure OPENAI_API_KEY, GEMINI_API_KEY, or start Ollama locally."
                ),
                raw_analysis=str(e),
                model_used="none",
                detailed_analysis=None,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception(
                "Unexpected error during AI diagnosis for pod '%s'", context.get("pod_name")
            )
            return DiagnoseResult(
                root_cause=f"Diagnosis failed: {e}",
                remediation="Check AI provider connectivity and retry.",
                raw_analysis=str(e),
                model_used="error",
                detailed_analysis=None,
            )

    def _parse_response(self, raw: str) -> ParsedResponse:
        """Extract structured fields from LLM JSON response."""
        # Extract content from markdown code fences if present.
        # Use non-greedy matching to capture only the first code block.
        code_fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
        if code_fence_match:
            raw = code_fence_match.group(1).strip()

        try:
            data = json.loads(raw)
            return ParsedResponse(
                root_cause=data.get("root_cause", ""),
                detailed_analysis=data.get("detailed_analysis") or None,
                remediation=data.get("remediation", ""),
            )
        except json.JSONDecodeError:
            # Graceful degradation: return raw text as root_cause
            return ParsedResponse(
                root_cause=raw[:500] if raw else "No analysis available",
                detailed_analysis=None,
                remediation="Review the raw analysis above for remediation steps.",
            )


if __name__ == '__main__':
    engine = AIDiagnoser()
    diagnosis_result = engine.diagnose({  # pylint: disable=invalid-name
        "pod_name": "test-pod",
        "namespace": "default",
        "error_type": "CrashLoopBackOff",
        "describe": "Phase: Failed",
        "logs": "Error: cannot connect to database",
    })
    print(diagnosis_result)
