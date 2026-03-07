"""Service layer orchestrating pod context collection and AI diagnosis."""
import logging
import os
from typing import TypedDict
import httpx
from sqlalchemy.orm import Session
from backend.models.schemas import DiagnoseResponse
from backend.models.orm_models import DiagnoseHistory
from backend.utils import mask_sensitive_data
from backend.services.pod_service import PodService

logger = logging.getLogger(__name__)


class AIResult(TypedDict):
    """Normalised AI diagnosis result returned by the AI engine (HTTP or local)."""

    root_cause: str
    detailed_analysis: str | None
    remediation: str
    raw_analysis: str
    model_used: str


class DiagnoseService:
    """Orchestrates AI-powered diagnosis by combining K8s context with LLM analysis."""

    def __init__(self) -> None:
        self._pod_service = PodService()
        self._ai_engine_url = os.getenv("AI_ENGINE_URL", "").rstrip("/")

    def diagnose(self, pod_name: str, namespace: str, db: Session) -> DiagnoseResponse:
        """Collect pod context, run AI analysis, persist result, and return structured response."""
        context = self._pod_service.get_pod_context(pod_name, namespace)

        masked_describe = mask_sensitive_data(context["describe"])
        masked_logs = mask_sensitive_data(context["logs"])

        payload = {
            "pod_name": pod_name,
            "namespace": namespace,
            "describe": masked_describe,
            "logs": masked_logs,
            "error_type": context["error_type"],
        }

        if self._ai_engine_url:
            result = self._call_ai_engine_service(payload)
        else:
            result = self._call_ai_engine_local(payload)

        record = DiagnoseHistory(
            pod_name=pod_name,
            namespace=namespace,
            error_type=context["error_type"],
            ai_analysis=result.get("raw_analysis", ""),
        )
        try:
            db.add(record)
            db.commit()
        except Exception as db_err:  # pylint: disable=broad-exception-caught
            db.rollback()
            logger.error(
                "Failed to persist diagnosis for pod %s/%s: %s", namespace, pod_name, db_err
            )

        return DiagnoseResponse(
            pod_name=pod_name,
            namespace=namespace,
            error_type=context["error_type"],
            root_cause=result["root_cause"],
            detailed_analysis=result["detailed_analysis"],
            remediation=result["remediation"],
            raw_analysis=result["raw_analysis"],
            model_used=result["model_used"],
        )

    def _call_ai_engine_service(self, payload: dict) -> AIResult:
        """Call the AI Engine microservice via HTTP."""
        try:
            with httpx.Client(timeout=120.0) as http_client:
                response = http_client.post(f"{self._ai_engine_url}/diagnose", json=payload)
                response.raise_for_status()
                data = response.json()
                return AIResult(
                    root_cause=data.get("root_cause", ""),
                    detailed_analysis=data.get("detailed_analysis") or None,
                    remediation=data.get("remediation", ""),
                    raw_analysis=data.get("raw_analysis", ""),
                    model_used=data.get("model_used", "unknown"),
                )
        except httpx.TimeoutException as e:
            return AIResult(
                root_cause="AI Engine service call timed out.",
                remediation="Check AI Engine service health and connectivity.",
                raw_analysis=str(e),
                model_used="error",
                detailed_analysis=None,
            )
        except httpx.HTTPStatusError as e:
            return AIResult(
                root_cause=f"AI Engine service returned HTTP {e.response.status_code}.",
                remediation="Check AI Engine service logs for details.",
                raw_analysis=str(e),
                model_used="error",
                detailed_analysis=None,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return AIResult(
                root_cause=f"AI Engine service call failed: {e}",
                remediation="Check AI Engine service connectivity.",
                raw_analysis=str(e),
                model_used="error",
                detailed_analysis=None,
            )

    def _call_ai_engine_local(self, payload: dict) -> AIResult:
        """Call AI Engine via direct Python import (local development)."""
        from ai_engine.diagnoser import AIDiagnoser  # pylint: disable=import-outside-toplevel
        diagnoser = AIDiagnoser()
        result = diagnoser.diagnose(payload)
        return AIResult(
            root_cause=result.get("root_cause", ""),
            detailed_analysis=result.get("detailed_analysis") or None,
            remediation=result.get("remediation", ""),
            raw_analysis=result.get("raw_analysis", ""),
            model_used=result.get("model_used", "unknown"),
        )
