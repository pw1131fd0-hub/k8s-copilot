from sqlalchemy.orm import Session
from backend.models.schemas import DiagnoseResponse
from backend.models.orm_models import DiagnoseHistory
from backend.utils import mask_sensitive_data
from backend.services.pod_service import PodService


class DiagnoseService:
    def __init__(self):
        self._pod_service = PodService()

    def diagnose(self, pod_name: str, namespace: str, db: Session) -> DiagnoseResponse:
        context = self._pod_service.get_pod_context(pod_name, namespace)

        masked_describe = mask_sensitive_data(context["describe"])
        masked_logs = mask_sensitive_data(context["logs"])

        from ai_engine.diagnoser import AIDiagnoser
        diagnoser = AIDiagnoser()
        result = diagnoser.diagnose({
            "pod_name": pod_name,
            "namespace": namespace,
            "describe": masked_describe,
            "logs": masked_logs,
            "error_type": context["error_type"],
        })

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
