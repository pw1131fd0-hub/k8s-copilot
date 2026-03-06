import os
import httpx
from sqlalchemy.orm import Session
from backend.models.schemas import DiagnoseResponse
from backend.models.orm_models import DiagnoseHistory
from backend.utils import mask_sensitive_data
from backend.services.pod_service import PodService


class DiagnoseService:
    def __init__(self):
        self._pod_service = PodService()
        self._ai_engine_url = os.getenv("AI_ENGINE_URL", "").rstrip("/")

    def diagnose(self, pod_name: str, namespace: str, db: Session) -> DiagnoseResponse:
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
        db.add(record)
        db.commit()

        return DiagnoseResponse(
            pod_name=pod_name,
            namespace=namespace,
            error_type=context["error_type"],
            root_cause=result.get("root_cause", ""),
            remediation=result.get("remediation", ""),
            raw_analysis=result.get("raw_analysis", ""),
            model_used=result.get("model_used", "unknown"),
        )

    def _call_ai_engine_service(self, payload: dict) -> dict:
        """Call the AI Engine microservice via HTTP."""
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self._ai_engine_url}/diagnose", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "root_cause": f"AI Engine service call failed: {e}",
                "remediation": "Check AI Engine service connectivity.",
                "raw_analysis": str(e),
                "model_used": "error",
            }

    def _call_ai_engine_local(self, payload: dict) -> dict:
        """Call AI Engine via direct Python import (local development)."""
        from ai_engine.diagnoser import AIDiagnoser
        diagnoser = AIDiagnoser()
        return diagnoser.diagnose(payload)
