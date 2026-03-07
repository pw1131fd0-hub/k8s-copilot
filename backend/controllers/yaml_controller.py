"""API controller for Kubernetes YAML manifest scanning and diffing."""
from typing import Any
from fastapi import APIRouter, Body, HTTPException
from backend.models.schemas import YamlScanRequest, YamlScanResponse
from backend.services.yaml_service import YamlService

router = APIRouter()
_svc = YamlService()

_YAML_DIFF_MAX_BYTES = 512 * 1024  # 512 KB per side


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
    for label, content in (("yaml_a", yaml_a), ("yaml_b", yaml_b)):
        if len(content.encode("utf-8")) > _YAML_DIFF_MAX_BYTES:
            raise HTTPException(
                status_code=422,
                detail=f"{label} exceeds maximum allowed size of {_YAML_DIFF_MAX_BYTES // 1024} KB",
            )
    return _svc.diff(yaml_a, yaml_b)
