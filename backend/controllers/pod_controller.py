"""API controller for Kubernetes pod listing endpoints."""
from fastapi import APIRouter, Query
from backend.models.schemas import PodListResponse
from backend.services.pod_service import PodService

router = APIRouter()
_svc = PodService()


@router.get("/pods", response_model=PodListResponse)
async def list_pods(
    namespace: str | None = Query(None, description="Filter by namespace"),
) -> PodListResponse:
    """Return all pods visible to the backend, optionally filtered by namespace."""
    return _svc.list_pods(namespace=namespace)
