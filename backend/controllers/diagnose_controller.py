from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.schemas import DiagnoseRequest, DiagnoseResponse, DiagnoseHistoryRecord
from backend.services.diagnose_service import DiagnoseService
from backend.repositories.diagnose_repository import DiagnoseRepository
from typing import List

router = APIRouter()
_svc = DiagnoseService()
_repo = DiagnoseRepository()


@router.post("/{pod_name}", response_model=DiagnoseResponse)
async def diagnose_pod(pod_name: str, request: DiagnoseRequest, db: Session = Depends(get_db)):
    try:
        return _svc.diagnose(pod_name=pod_name, namespace=request.namespace, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[DiagnoseHistoryRecord])
async def get_diagnose_history(db: Session = Depends(get_db)):
    return _repo.get_history(db)


@router.get("/history/{pod_name}", response_model=List[DiagnoseHistoryRecord])
async def get_pod_diagnose_history(pod_name: str, db: Session = Depends(get_db)):
    return _repo.get_by_pod(db, pod_name)
