from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
