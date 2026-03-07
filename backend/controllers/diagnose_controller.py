"""API controller for AI-powered pod diagnosis and history retrieval."""
import logging
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.schemas import DiagnoseRequest, DiagnoseResponse, DiagnoseHistoryRecord
from backend.services.diagnose_service import DiagnoseService
from backend.repositories.diagnose_repository import DiagnoseRepository
from backend.utils import K8S_NAME_RE, PodNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()
_svc = DiagnoseService()
_repo = DiagnoseRepository()


@router.post("/{pod_name}", response_model=DiagnoseResponse)
async def diagnose_pod(
    pod_name: str = Path(..., description="Kubernetes pod name"),
    request: DiagnoseRequest = Body(...),
    db: Session = Depends(get_db),
) -> DiagnoseResponse:
    """Trigger AI diagnosis for a pod and persist the result to history."""
    if not K8S_NAME_RE.match(pod_name):
        raise HTTPException(status_code=422, detail="Invalid pod name format")
    try:
        return _svc.diagnose(pod_name=pod_name, namespace=request.namespace, db=db)
    except PodNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Diagnosis failed for pod %s: %s", pod_name, e)
        raise HTTPException(
            status_code=500, detail="Diagnosis failed. Check server logs for details."
        ) from e


@router.get("/history", response_model=list[DiagnoseHistoryRecord])
async def get_diagnose_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> list[DiagnoseHistoryRecord]:
    """Return recent diagnosis records across all pods, ordered by creation time descending."""
    return _repo.get_history(db, limit=limit)


@router.get("/history/{pod_name}", response_model=list[DiagnoseHistoryRecord])
async def get_pod_diagnose_history(
    pod_name: str = Path(..., description="Kubernetes pod name"),
    db: Session = Depends(get_db),
) -> list[DiagnoseHistoryRecord]:
    """Return diagnosis history for a specific pod, newest first."""
    if not K8S_NAME_RE.match(pod_name):
        raise HTTPException(status_code=422, detail="Invalid pod name format")
    return _repo.get_by_pod(db, pod_name)
