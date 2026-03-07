"""Pydantic request/response schemas for the Lobster K8s Copilot API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from backend.utils import K8S_NAME_RE

_YAML_MAX_BYTES = 512 * 1024  # 512 KB


class PodInfo(BaseModel):
    """Represents a single Kubernetes pod with basic status fields."""

    name: str
    namespace: str
    status: str | None
    ip: str | None
    conditions: list[dict] = []


class PodListResponse(BaseModel):
    """Response model for pod listing endpoints."""

    pods: list[PodInfo]
    total: int


class DiagnoseRequest(BaseModel):
    """Request body for triggering AI diagnosis on a pod."""

    namespace: str = "default"
    force: bool = False

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Ensure namespace follows Kubernetes DNS-subdomain naming rules."""
        if not K8S_NAME_RE.match(v):
            raise ValueError(
                "namespace must be a valid Kubernetes name (lowercase alphanumeric and hyphens)"
            )
        return v


class DiagnoseResponse(BaseModel):
    """Response model containing AI-generated diagnosis for a Kubernetes pod."""

    pod_name: str
    namespace: str
    error_type: str | None
    root_cause: str
    detailed_analysis: str | None = None
    remediation: str
    raw_analysis: str
    model_used: str


class YamlScanRequest(BaseModel):
    """Request body for YAML manifest scanning."""

    yaml_content: str
    filename: str | None = "manifest.yaml"

    @field_validator("yaml_content")
    @classmethod
    def validate_yaml_size(cls, v: str) -> str:
        """Reject YAML payloads exceeding the maximum allowed byte size."""
        if len(v.encode("utf-8")) > _YAML_MAX_BYTES:
            raise ValueError(
                f"yaml_content exceeds maximum allowed size of {_YAML_MAX_BYTES // 1024} KB"
            )
        return v


class YamlIssue(BaseModel):
    """A single issue detected during YAML manifest scanning."""

    severity: Literal["ERROR", "WARNING", "INFO"]
    rule: str
    message: str
    line: int | None = None


class YamlScanResponse(BaseModel):
    """Response model for YAML scan results, including all detected issues."""

    filename: str
    issues: list[YamlIssue]
    total_issues: int
    has_errors: bool
    ai_suggestions: str | None = None


class DiagnoseHistoryRecord(BaseModel):
    """A persisted diagnosis record retrieved from the database."""

    id: str
    pod_name: str
    namespace: str
    error_type: str | None
    ai_analysis: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
