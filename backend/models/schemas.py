"""Pydantic request/response schemas for the Lobster K8s Copilot API."""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from backend.utils import K8S_NAME_RE

_YAML_MAX_BYTES = 512 * 1024  # 512 KB


class PodInfo(BaseModel):
    name: str
    namespace: str
    status: Optional[str]
    ip: Optional[str]
    conditions: Optional[List[dict]] = []


class PodListResponse(BaseModel):
    pods: List[PodInfo]
    total: int


class DiagnoseRequest(BaseModel):
    namespace: str = "default"
    force: bool = False

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        if not K8S_NAME_RE.match(v):
            raise ValueError("namespace must be a valid Kubernetes name (lowercase alphanumeric and hyphens)")
        return v


class DiagnoseResponse(BaseModel):
    pod_name: str
    namespace: str
    error_type: Optional[str]
    root_cause: str
    remediation: str
    raw_analysis: str
    model_used: str


class YamlScanRequest(BaseModel):
    yaml_content: str
    filename: Optional[str] = "manifest.yaml"

    @field_validator("yaml_content")
    @classmethod
    def validate_yaml_size(cls, v: str) -> str:
        if len(v.encode("utf-8")) > _YAML_MAX_BYTES:
            raise ValueError(f"yaml_content exceeds maximum allowed size of {_YAML_MAX_BYTES // 1024} KB")
        return v


class YamlIssue(BaseModel):
    severity: str  # ERROR | WARNING | INFO
    rule: str
    message: str
    line: Optional[int] = None


class YamlScanResponse(BaseModel):
    filename: str
    issues: List[YamlIssue]
    total_issues: int
    has_errors: bool
    ai_suggestions: Optional[str] = None


class DiagnoseHistoryRecord(BaseModel):
    id: str
    pod_name: str
    namespace: str
    error_type: Optional[str]
    ai_analysis: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
