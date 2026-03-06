from typing import Any, Dict, List
import yaml
from backend.models.schemas import YamlIssue, YamlScanResponse
from deepdiff import DeepDiff


ANTI_PATTERN_RULES: List[Dict[str, Any]] = [
    {
        "id": "no-resource-limits",
        "severity": "ERROR",
        "message": "Container '{container}' is missing CPU/Memory resource limits. Set resources.limits to prevent OOM.",
        "check": lambda c: not (c.get("resources", {}).get("limits")),
    },
    {
        "id": "no-resource-requests",
        "severity": "WARNING",
        "message": "Container '{container}' is missing resource requests. Set resources.requests for proper scheduling.",
        "check": lambda c: not (c.get("resources", {}).get("requests")),
    },
    {
        "id": "privileged-container",
        "severity": "ERROR",
        "message": "Container '{container}' is running in privileged mode. Remove securityContext.privileged or set to false.",
        "check": lambda c: c.get("securityContext", {}).get("privileged") is True,
    },
    {
        "id": "run-as-root",
        "severity": "ERROR",
        "message": "Container '{container}' may run as root. Set securityContext.runAsNonRoot: true.",
        "check": lambda c: not c.get("securityContext", {}).get("runAsNonRoot"),
    },
    {
        "id": "no-liveness-probe",
        "severity": "WARNING",
        "message": "Container '{container}' has no livenessProbe. Add a livenessProbe for automatic recovery.",
        "check": lambda c: not c.get("livenessProbe"),
    },
    {
        "id": "no-readiness-probe",
        "severity": "WARNING",
        "message": "Container '{container}' has no readinessProbe. Add a readinessProbe to control traffic routing.",
        "check": lambda c: not c.get("readinessProbe"),
    },
    {
        "id": "latest-image-tag",
        "severity": "WARNING",
        "message": "Container '{container}' uses 'latest' image tag. Pin to a specific version for reproducibility.",
        "check": lambda c: c.get("image", "").endswith(":latest") or ":" not in c.get("image", ""),
    },
]


class YamlService:
    def scan(self, yaml_content: str, filename: str = "manifest.yaml") -> YamlScanResponse:
        issues: List[YamlIssue] = []

        try:
            docs = list(yaml.safe_load_all(yaml_content))
        except yaml.YAMLError as e:
            return YamlScanResponse(
                filename=filename,
                issues=[YamlIssue(severity="ERROR", rule="yaml-parse-error", message=str(e))],
                total_issues=1,
                has_errors=True,
            )

        for doc in docs:
            if not doc or not isinstance(doc, dict):
                continue

            kind = doc.get("kind", "")
            spec = doc.get("spec", {})
            containers = []

            # Extract containers from Deployment/DaemonSet/StatefulSet/Job/CronJob
            if kind in ("Deployment", "DaemonSet", "StatefulSet", "ReplicaSet"):
                containers = spec.get("template", {}).get("spec", {}).get("containers", [])
            elif kind == "Pod":
                containers = spec.get("containers", [])
            elif kind == "CronJob":
                containers = (spec.get("jobTemplate", {}).get("spec", {})
                              .get("template", {}).get("spec", {}).get("containers", []))

            for container in containers:
                name = container.get("name", "unknown")
                for rule in ANTI_PATTERN_RULES:
                    if rule["check"](container):
                        issues.append(YamlIssue(
                            severity=rule["severity"],
                            rule=rule["id"],
                            message=rule["message"].format(container=name),
                        ))

        has_errors = any(i.severity == "ERROR" for i in issues)
        return YamlScanResponse(
            filename=filename,
            issues=issues,
            total_issues=len(issues),
            has_errors=has_errors,
        )

    def diff(self, yaml_a: str, yaml_b: str) -> dict:
        """Compare two YAML strings and return their differences."""
        try:
            doc_a = yaml.safe_load(yaml_a)
            doc_b = yaml.safe_load(yaml_b)
            diff = DeepDiff(doc_a, doc_b, ignore_order=True)
            return diff.to_dict() if diff else {}
        except Exception as e:
            return {"error": str(e)}
