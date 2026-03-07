"""API controller for Kubernetes YAML manifest scanning and diffing."""
from typing import Any
from fastapi import APIRouter, Body
from backend.models.schemas import YamlScanRequest, YamlScanResponse
from backend.services.yaml_service import YamlService

router = APIRouter()
_svc = YamlService()


@router.post("/scan", response_model=YamlScanResponse)
async def scan_yaml(request: YamlScanRequest) -> YamlScanResponse:
    """Scan a Kubernetes YAML manifest for security and reliability anti-patterns."""
    return _svc.scan(request.yaml_content, filename=request.filename or "manifest.yaml")


@router.post("/diff")
async def diff_yaml(
    yaml_a: str = Body(..., embed=True),
    yaml_b: str = Body(..., embed=True),
) -> dict[str, Any]:
    """Return a deep-diff between two YAML manifests."""
    return _svc.diff(yaml_a, yaml_b)
