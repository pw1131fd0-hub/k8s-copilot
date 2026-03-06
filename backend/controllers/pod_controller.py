from fastapi import APIRouter, Query
from typing import Optional
from backend.models.schemas import PodListResponse
from backend.services.pod_service import PodService

router = APIRouter()
_svc = PodService()


@router.get("/pods", response_model=PodListResponse)
async def list_pods(namespace: Optional[str] = Query(None, description="Filter by namespace")):
    return _svc.list_pods(namespace=namespace)
