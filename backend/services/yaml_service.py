"""Service layer for Kubernetes YAML manifest scanning and diff operations."""
import logging
import os
from typing import Any
import httpx
import yaml
from deepdiff import DeepDiff
from backend.models.schemas import YamlIssue, YamlScanResponse

logger = logging.getLogger(__name__)

# Maximum characters of YAML content sent to the AI engine to keep prompts within token limits.
_YAML_AI_TRUNCATE_CHARS = 3000


ANTI_PATTERN_RULES: list[dict[str, Any]] = [
    {
        "id": "no-resource-limits",
        "severity": "ERROR",
        "message": (
            "Container '{container}' is missing CPU/Memory resource limits."
            " Set resources.limits to prevent OOM."
        ),
        "check": lambda c: not (c.get("resources", {}).get("limits")),
    },
    {
        "id": "no-resource-requests",
        "severity": "WARNING",
        "message": (
            "Container '{container}' is missing resource requests."
            " Set resources.requests for proper scheduling."
        ),
        "check": lambda c: not (c.get("resources", {}).get("requests")),
    },
    {
        "id": "privileged-container",
        "severity": "ERROR",
        "message": (
            "Container '{container}' is running in privileged mode."
            " Remove securityContext.privileged or set to false."
        ),
        "check": lambda c: c.get("securityContext", {}).get("privileged") is True,
    },
    {
        "id": "run-as-root",
        "severity": "ERROR",
        "message": (
            "Container '{container}' may run as root."
            " Set securityContext.runAsNonRoot: true."
        ),
        "check": lambda c: not c.get("securityContext", {}).get("runAsNonRoot"),
    },
    {
        "id": "no-liveness-probe",
        "severity": "WARNING",
        "message": (
            "Container '{container}' has no livenessProbe."
            " Add a livenessProbe for automatic recovery."
        ),
        "check": lambda c: not c.get("livenessProbe"),
    },
    {
        "id": "no-readiness-probe",
        "severity": "WARNING",
        "message": (
            "Container '{container}' has no readinessProbe."
            " Add a readinessProbe to control traffic routing."
        ),
        "check": lambda c: not c.get("readinessProbe"),
    },
    {
        "id": "latest-image-tag",
        "severity": "WARNING",
        "message": (
            "Container '{container}' uses 'latest' image tag."
            " Pin to a specific version for reproducibility."
        ),
        "check": lambda c: c.get("image", "").endswith(":latest") or ":" not in c.get("image", ""),
    },
]


class YamlService:
    """Scans Kubernetes YAML manifests for security and reliability anti-patterns."""

    def scan(self, yaml_content: str, filename: str = "manifest.yaml") -> YamlScanResponse:
        """Parse and analyse a multi-document YAML manifest, returning all detected issues."""
        issues: list[YamlIssue] = []

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
            elif kind == "Job":
                containers = spec.get("template", {}).get("spec", {}).get("containers", [])

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
        ai_suggestions = self._get_ai_suggestions(issues, yaml_content) if issues else None
        return YamlScanResponse(
            filename=filename,
            issues=issues,
            total_issues=len(issues),
            has_errors=has_errors,
            ai_suggestions=ai_suggestions,
        )

    def _get_ai_suggestions(self, issues: list[YamlIssue], yaml_content: str) -> str | None:
        """Call AI engine for human-friendly remediation advice on detected issues (best-effort)."""
        ai_engine_url = os.getenv("AI_ENGINE_URL", "").rstrip("/")
        if ai_engine_url:
            return self._get_ai_suggestions_via_http(issues, yaml_content, ai_engine_url)
        return self._get_ai_suggestions_local(issues, yaml_content)

    def _get_ai_suggestions_via_http(
        self, issues: list[YamlIssue], yaml_content: str, ai_engine_url: str
    ) -> str | None:
        """Fetch AI suggestions from the AI Engine microservice via HTTP."""
        from ai_engine.prompts.k8s_prompts import YAML_SCAN_PROMPT_TEMPLATE  # pylint: disable=import-outside-toplevel
        issues_text = "\n".join(f"- [{i.severity}] {i.rule}: {i.message}" for i in issues)
        prompt = YAML_SCAN_PROMPT_TEMPLATE.format(
            issues=issues_text,
            yaml_content=yaml_content[:_YAML_AI_TRUNCATE_CHARS],
        )
        try:
            with httpx.Client(timeout=30.0) as http:
                resp = http.post(f"{ai_engine_url}/suggest", json={"prompt": prompt})
                resp.raise_for_status()
                return resp.json().get("suggestion") or None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("AI suggestions via HTTP failed: %s", e)
            return None

    def _get_ai_suggestions_local(
        self, issues: list[YamlIssue], yaml_content: str
    ) -> str | None:
        """Fetch AI suggestions using the local AIDiagnoser import (development mode)."""
        try:
            from ai_engine.diagnoser import AIDiagnoser  # pylint: disable=import-outside-toplevel
            from ai_engine.prompts.k8s_prompts import YAML_SCAN_PROMPT_TEMPLATE  # pylint: disable=import-outside-toplevel
            issues_text = "\n".join(f"- [{i.severity}] {i.rule}: {i.message}" for i in issues)
            prompt = YAML_SCAN_PROMPT_TEMPLATE.format(
                issues=issues_text,
                yaml_content=yaml_content[:_YAML_AI_TRUNCATE_CHARS],
            )
            result = AIDiagnoser().suggest(prompt)
            return result or None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("AI suggestions via local import failed: %s", e)
            return None

    def diff(self, yaml_a: str, yaml_b: str) -> dict[str, Any]:
        """Compare two YAML strings and return their differences."""
        try:
            doc_a = yaml.safe_load(yaml_a)
            doc_b = yaml.safe_load(yaml_b)
            diff = DeepDiff(doc_a, doc_b, ignore_order=True)
            return diff.to_dict() if diff else {}
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {"error": str(e)}
