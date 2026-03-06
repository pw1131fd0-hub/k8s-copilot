"""API controller for AI-powered pod diagnosis and history retrieval."""
import logging
import re
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.schemas import DiagnoseRequest, DiagnoseResponse, DiagnoseHistoryRecord
from backend.services.diagnose_service import DiagnoseService
from backend.repositories.diagnose_repository import DiagnoseRepository
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()
_svc = DiagnoseService()
_repo = DiagnoseRepository()


_POD_NAME_RE = re.compile(r'^[a-z0-9]([a-z0-9\-]{0,251}[a-z0-9])?$')


@router.post("/{pod_name}", response_model=DiagnoseResponse)
async def diagnose_pod(
    pod_name: str = Path(..., description="Kubernetes pod name"),
    request: DiagnoseRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Trigger AI diagnosis for a pod and persist the result to history."""
    if not _POD_NAME_RE.match(pod_name):
        raise HTTPException(status_code=422, detail="Invalid pod name format")
    try:
        return _svc.diagnose(pod_name=pod_name, namespace=request.namespace, db=db)
    except Exception as e:
        logger.error("Diagnosis failed for pod %s: %s", pod_name, e)
        raise HTTPException(status_code=500, detail="Diagnosis failed. Check server logs for details.")


@router.get("/history", response_model=List[DiagnoseHistoryRecord])
async def get_diagnose_history(db: Session = Depends(get_db)):
    """Return the 50 most recent diagnosis records across all pods."""
    return _repo.get_history(db)


@router.get("/history/{pod_name}", response_model=List[DiagnoseHistoryRecord])
async def get_pod_diagnose_history(
    pod_name: str = Path(..., description="Kubernetes pod name"),
    db: Session = Depends(get_db),
):
    """Return diagnosis history for a specific pod, newest first."""
    if not _POD_NAME_RE.match(pod_name):
        raise HTTPException(status_code=422, detail="Invalid pod name format")
    return _repo.get_by_pod(db, pod_name)
