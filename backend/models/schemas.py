"""Pydantic request/response schemas for the Lobster K8s Copilot API."""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from backend.utils import K8S_NAME_RE

_YAML_MAX_BYTES = 512 * 1024  # 512 KB


class PodInfo(BaseModel):
    """Represents a single Kubernetes pod with basic status fields."""

    name: str
    namespace: str
    status: Optional[str]
    ip: Optional[str]
    conditions: Optional[List[dict]] = []


class PodListResponse(BaseModel):
    """Response model for pod listing endpoints."""

    pods: List[PodInfo]
    total: int


class DiagnoseRequest(BaseModel):
    """Request body for triggering AI diagnosis on a pod."""

    namespace: str = "default"
    force: bool = False

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        if not K8S_NAME_RE.match(v):
            raise ValueError("namespace must be a valid Kubernetes name (lowercase alphanumeric and hyphens)")
        return v


class DiagnoseResponse(BaseModel):
    """Response model containing AI-generated diagnosis for a Kubernetes pod."""

    pod_name: str
    namespace: str
    error_type: Optional[str]
    root_cause: str
    remediation: str
    raw_analysis: str
    model_used: str


class YamlScanRequest(BaseModel):
    """Request body for YAML manifest scanning."""

    yaml_content: str
    filename: Optional[str] = "manifest.yaml"

    @field_validator("yaml_content")
    @classmethod
    def validate_yaml_size(cls, v: str) -> str:
        if len(v.encode("utf-8")) > _YAML_MAX_BYTES:
            raise ValueError(f"yaml_content exceeds maximum allowed size of {_YAML_MAX_BYTES // 1024} KB")
        return v


class YamlIssue(BaseModel):
    """A single issue detected during YAML manifest scanning."""

    severity: str  # ERROR | WARNING | INFO
    rule: str
    message: str
    line: Optional[int] = None


class YamlScanResponse(BaseModel):
    """Response model for YAML scan results, including all detected issues."""

    filename: str
    issues: List[YamlIssue]
    total_issues: int
    has_errors: bool
    ai_suggestions: Optional[str] = None


class DiagnoseHistoryRecord(BaseModel):
    """A persisted diagnosis record retrieved from the database."""

    id: str
    pod_name: str
    namespace: str
    error_type: Optional[str]
    ai_analysis: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
