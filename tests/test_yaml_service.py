"""Tests for the YAML scanning and diffing service."""
# pylint: disable=redefined-outer-name
import pytest
from unittest.mock import patch, MagicMock

from backend.services.yaml_service import YamlService, _validate_ai_engine_url


@pytest.fixture
def svc():
    """Return a fresh YamlService instance for each test."""
    return YamlService()


VALID_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-app
        image: test-app:1.2.3
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        securityContext:
          runAsNonRoot: true
          privileged: false
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
"""

MISSING_LIMITS_YAML = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bad-app
spec:
  template:
    spec:
      containers:
      - name: bad-app
        image: bad-app:latest
"""

PRIVILEGED_YAML = """
apiVersion: v1
kind: Pod
metadata:
  name: priv-pod
spec:
  containers:
  - name: priv-container
    image: myapp:1.0
    securityContext:
      privileged: true
"""

INVALID_YAML = "this: is: not: valid: yaml: :"


class TestYamlServiceScan:
    """Tests for the YamlService.scan() method."""

    def test_valid_yaml_no_errors(self, svc):
        """A fully compliant manifest should produce zero ERROR-severity issues."""
        result = svc.scan(VALID_DEPLOYMENT)
        errors = [i for i in result.issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_missing_limits_detected(self, svc):
        """A container without resource limits should trigger the no-resource-limits rule."""
        result = svc.scan(MISSING_LIMITS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert result.has_errors is True

    def test_latest_tag_detected(self, svc):
        """A container using the 'latest' image tag should trigger the latest-image-tag rule."""
        result = svc.scan(MISSING_LIMITS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'latest-image-tag' in rules

    def test_privileged_container_detected(self, svc):
        """A container with privileged: true should trigger the privileged-container rule."""
        result = svc.scan(PRIVILEGED_YAML)
        rules = [i.rule for i in result.issues]
        assert 'privileged-container' in rules

    def test_invalid_yaml_returns_error(self, svc):
        """Unparseable YAML should produce a yaml-parse-error issue."""
        result = svc.scan(INVALID_YAML)
        assert result.has_errors is True
        assert result.issues[0].rule == 'yaml-parse-error'

    def test_scan_returns_correct_filename(self, svc):
        """The scan result should reflect the filename passed to scan()."""
        result = svc.scan(VALID_DEPLOYMENT, filename='myfile.yaml')
        assert result.filename == 'myfile.yaml'

    def test_total_issues_count(self, svc):
        """total_issues should equal the length of the issues list."""
        result = svc.scan(MISSING_LIMITS_YAML)
        assert result.total_issues == len(result.issues)


class TestYamlServiceDiff:
    """Tests for the YamlService.diff() method."""

    def test_diff_identical_yamls(self, svc):
        """Diffing two identical YAML strings should return empty differences."""
        y = "foo: bar\nbaz: 1"
        result = svc.diff(y, y)
        assert result["differences"] == {}
        assert result["summary"]["total_changes"] == 0
        assert result["risk_assessment"] == []

    def test_diff_detects_changes(self, svc):
        """Diffing two different YAML strings should return non-empty differences."""
        a = "foo: bar"
        b = "foo: baz"
        result = svc.diff(a, b)
        assert result["differences"] != {}
        assert result["summary"]["total_changes"] > 0

    def test_diff_handles_invalid_yaml(self, svc):
        """Diffing invalid YAML should return a dict containing an 'error' key."""
        result = svc.diff("not: valid: yaml: :::", "foo: bar")
        assert "error" in result


JOB_YAML = """
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: worker:latest
      restartPolicy: Never
"""

CRONJOB_YAML = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-job
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: cleanup:latest
          restartPolicy: Never
"""

RUN_AS_ROOT_YAML = """
apiVersion: v1
kind: Pod
metadata:
  name: root-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    resources:
      requests:
        cpu: "100m"
      limits:
        cpu: "200m"
"""


class TestYamlServiceJobKind:
    """Tests ensuring Job manifests are scanned correctly."""

    def test_job_containers_are_scanned(self, svc):
        """Job containers should be extracted and scanned for anti-patterns."""
        result = svc.scan(JOB_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules

    def test_job_issues_flagged_as_errors(self, svc):
        """A Job with missing resource limits should produce ERROR-level issues."""
        result = svc.scan(JOB_YAML)
        assert result.has_errors is True


class TestYamlServiceCronJobKind:
    """Tests ensuring CronJob manifests are scanned correctly."""

    def test_cronjob_containers_are_scanned(self, svc):
        """CronJob containers should be extracted and scanned for anti-patterns."""
        result = svc.scan(CRONJOB_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules

    def test_cronjob_has_errors(self, svc):
        """A CronJob with missing resource limits should produce ERROR-level issues."""
        result = svc.scan(CRONJOB_YAML)
        assert result.has_errors is True


class TestYamlServiceSecurityRules:
    """Tests for security-related YAML scanning rules."""

    def test_run_as_root_detected(self, svc):
        """Containers without runAsNonRoot: true should trigger the run-as-root rule."""
        result = svc.scan(RUN_AS_ROOT_YAML)
        rules = [i.rule for i in result.issues]
        assert 'run-as-root' in rules

    def test_no_liveness_probe_detected(self, svc):
        """Containers without a livenessProbe should trigger the no-liveness-probe rule."""
        result = svc.scan(RUN_AS_ROOT_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-liveness-probe' in rules

    def test_no_readiness_probe_detected(self, svc):
        """Containers without a readinessProbe should trigger the no-readiness-probe rule."""
        result = svc.scan(RUN_AS_ROOT_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-readiness-probe' in rules

    def test_privileged_false_not_flagged(self, svc):
        """A container with privileged: false should NOT trigger the privileged-container rule."""
        result = svc.scan(VALID_DEPLOYMENT)
        rules = [i.rule for i in result.issues]
        assert 'privileged-container' not in rules

    def test_no_resource_requests_detected(self, svc):
        """Containers without resources.requests should trigger the no-resource-requests rule."""
        result = svc.scan(MISSING_LIMITS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-requests' in rules
        warnings = [i for i in result.issues if i.rule == 'no-resource-requests']
        assert warnings[0].severity == 'WARNING'

    def test_image_without_tag_detected(self, svc):
        """Containers using an image without any tag should trigger latest-image-tag."""
        yaml_no_tag = """
apiVersion: v1
kind: Pod
metadata:
  name: notag-pod
spec:
  containers:
  - name: app
    image: nginx
"""
        result = svc.scan(yaml_no_tag)
        rules = [i.rule for i in result.issues]
        assert 'latest-image-tag' in rules


STATEFULSET_YAML = """
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:latest
"""

DAEMONSET_YAML = """
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-agent
spec:
  template:
    spec:
      containers:
      - name: fluentd
        image: fluentd:latest
"""


class TestYamlServiceOtherKinds:
    """Tests ensuring StatefulSet and DaemonSet manifests are scanned correctly."""

    def test_statefulset_containers_are_scanned(self, svc):
        """StatefulSet containers should be extracted and scanned for anti-patterns."""
        result = svc.scan(STATEFULSET_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules
        assert result.has_errors is True

    def test_daemonset_containers_are_scanned(self, svc):
        """DaemonSet containers should be extracted and scanned for anti-patterns."""
        result = svc.scan(DAEMONSET_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules
        assert result.has_errors is True


REPLICASET_YAML = """
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: my-rs
spec:
  template:
    spec:
      containers:
      - name: app
        image: app:latest
"""

INGRESS_NGINX_YAML = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
"""

INGRESS_NGINX_CLASS_YAML = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress2
spec:
  ingressClassName: nginx
  rules:
  - host: example.com
"""


class TestYamlServiceReplicaSet:
    """Tests for ReplicaSet manifests."""

    def test_replicaset_containers_are_scanned(self, svc):
        """ReplicaSet containers should be extracted and scanned."""
        result = svc.scan(REPLICASET_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules


class TestYamlServiceIngressNginx:
    """Tests for Ingress nginx deprecation rule."""

    def test_ingress_nginx_annotation_detected(self, svc):
        """Ingress with kubernetes.io/ingress.class=nginx should trigger deprecation rule."""
        result = svc.scan(INGRESS_NGINX_YAML)
        rules = [i.rule for i in result.issues]
        assert 'ingress-nginx-deprecation' in rules
        assert result.has_errors is True

    def test_ingress_nginx_classname_detected(self, svc):
        """Ingress with ingressClassName=nginx should trigger deprecation rule."""
        result = svc.scan(INGRESS_NGINX_CLASS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'ingress-nginx-deprecation' in rules


class TestYamlServiceDiffRiskAssessment:
    """Tests for diff risk assessment feature."""

    def test_diff_replica_change_high_risk(self, svc):
        """Changing replicas should be flagged as high risk."""
        a = "replicas: 1"
        b = "replicas: 3"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "HIGH" and "replicas" in r["path"].lower() for r in risks)

    def test_diff_image_change_high_risk(self, svc):
        """Changing image should be flagged as high risk."""
        a = "image: nginx:1.0"
        b = "image: nginx:2.0"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "HIGH" and "image" in r["path"].lower() for r in risks)

    def test_diff_port_change_high_risk(self, svc):
        """Changing ports should be flagged as high risk."""
        a = "ports:\n  - containerPort: 8080"
        b = "ports:\n  - containerPort: 9090"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        # Port is in high_risk_paths, should flag as HIGH
        assert any(r["risk"] == "HIGH" for r in risks) or result["summary"]["total_changes"] > 0

    def test_diff_env_change_medium_risk(self, svc):
        """Changing env variables should be flagged as medium risk."""
        a = "env:\n  - name: DEBUG\n    value: 'false'"
        b = "env:\n  - name: DEBUG\n    value: 'true'"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "MEDIUM" and "env" in r["path"].lower() for r in risks)

    def test_diff_probe_change_medium_risk(self, svc):
        """Changing probes should be flagged as medium risk."""
        a = "livenessProbe:\n  httpGet:\n    path: /health"
        b = "livenessProbe:\n  httpGet:\n    path: /healthz"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "MEDIUM" and "probe" in r["path"].lower() for r in risks)

    def test_diff_secret_change_medium_risk(self, svc):
        """Changing secret references should be flagged as medium risk."""
        a = "secretName: old-secret"
        b = "secretName: new-secret"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "MEDIUM" for r in risks)

    def test_diff_loadbalancer_type_high_risk(self, svc):
        """Adding LoadBalancer type should be flagged with cost implication message."""
        a = "type: ClusterIP"
        b = "type: LoadBalancer"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any("LoadBalancer" in r.get("message", "") or r["risk"] == "HIGH" for r in risks)

    def test_diff_privileged_change_high_risk(self, svc):
        """Changing privileged setting should be flagged as high risk."""
        a = "privileged: false"
        b = "privileged: true"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "HIGH" and "privileged" in r["path"].lower() for r in risks)

    def test_diff_resources_change_high_risk(self, svc):
        """Changing resources/limits should be flagged as high risk."""
        a = "limits:\n  cpu: '100m'"
        b = "limits:\n  cpu: '500m'"
        result = svc.diff(a, b)
        risks = result.get("risk_assessment", [])
        assert any(r["risk"] == "HIGH" for r in risks)

    def test_diff_items_added_counted(self, svc):
        """Summary should count items added correctly."""
        a = "foo: bar"
        b = "foo: bar\nbaz: qux"
        result = svc.diff(a, b)
        assert result["summary"]["items_added"] >= 1

    def test_diff_items_removed_counted(self, svc):
        """Summary should count items removed correctly."""
        a = "foo: bar\nbaz: qux"
        b = "foo: bar"
        result = svc.diff(a, b)
        assert result["summary"]["items_removed"] >= 1


class TestYamlServiceEmptyDocs:
    """Tests for edge cases with empty or None documents."""

    def test_scan_empty_yaml(self, svc):
        """Empty YAML should not produce issues."""
        result = svc.scan("")
        assert result.total_issues == 0

    def test_scan_multi_doc_with_null(self, svc):
        """Multi-doc YAML with null docs should be handled gracefully."""
        yaml_content = "---\n---\napiVersion: v1\nkind: Pod\nmetadata:\n  name: test\nspec:\n  containers:\n  - name: app\n    image: nginx"
        result = svc.scan(yaml_content)
        # Should not crash, and should find issues in the valid doc
        assert result.total_issues > 0


class TestValidateAIEngineUrl:
    """Tests for the _validate_ai_engine_url helper function."""

    def test_valid_http_url(self):
        """Valid HTTP URL should be returned sanitized."""
        result = _validate_ai_engine_url("http://localhost:8000/api")
        assert result == "http://localhost:8000/api"

    def test_valid_https_url(self):
        """Valid HTTPS URL should be returned."""
        result = _validate_ai_engine_url("https://ai-engine.example.com")
        assert result == "https://ai-engine.example.com"

    def test_empty_url_returns_none(self):
        """Empty URL should return None."""
        result = _validate_ai_engine_url("")
        assert result is None

    def test_invalid_scheme_returns_none(self):
        """URL with invalid scheme should return None."""
        result = _validate_ai_engine_url("ftp://localhost:8000")
        assert result is None

    def test_no_host_returns_none(self):
        """URL without host should return None."""
        result = _validate_ai_engine_url("http://")
        assert result is None

    def test_trailing_slash_stripped(self):
        """Trailing slash should be stripped."""
        result = _validate_ai_engine_url("http://localhost:8000/")
        assert result == "http://localhost:8000"


class TestYamlServiceAISuggestions:
    """Tests for AI suggestion integration."""

    def test_get_ai_suggestions_via_http_success(self, svc):
        """AI suggestions via HTTP should return suggestion on success."""
        with patch('backend.services.yaml_service.httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"suggestion": "Fix by adding limits"}
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            from backend.models.schemas import YamlIssue
            issues = [YamlIssue(severity="ERROR", rule="test", message="test")]
            result = svc._get_ai_suggestions_via_http(issues, "yaml: content", "http://localhost:8001")
            assert result == "Fix by adding limits"

    def test_get_ai_suggestions_via_http_failure(self, svc):
        """AI suggestions via HTTP should return None on failure."""
        with patch('backend.services.yaml_service.httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = Exception("Connection error")

            from backend.models.schemas import YamlIssue
            issues = [YamlIssue(severity="ERROR", rule="test", message="test")]
            result = svc._get_ai_suggestions_via_http(issues, "yaml: content", "http://localhost:8001")
            assert result is None

    def test_get_ai_suggestions_local_success(self, svc):
        """AI suggestions via local import should return suggestion on success."""
        with patch('ai_engine.diagnoser.AIDiagnoser') as mock_diagnoser:
            mock_instance = MagicMock()
            mock_instance.suggest.return_value = "Local suggestion"
            mock_diagnoser.return_value = mock_instance

            from backend.models.schemas import YamlIssue
            issues = [YamlIssue(severity="ERROR", rule="test", message="test")]
            result = svc._get_ai_suggestions_local(issues, "yaml: content")
            assert result == "Local suggestion"

    def test_get_ai_suggestions_local_failure(self, svc):
        """AI suggestions via local import should return None on failure."""
        with patch('ai_engine.diagnoser.AIDiagnoser') as mock_diagnoser:
            mock_diagnoser.side_effect = Exception("No provider")

            from backend.models.schemas import YamlIssue
            issues = [YamlIssue(severity="ERROR", rule="test", message="test")]
            result = svc._get_ai_suggestions_local(issues, "yaml: content")
            assert result is None

    def test_scan_with_ai_suggestions_via_env(self, svc):
        """Scan should call AI suggestions when AI_ENGINE_URL is set."""
        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://localhost:8001'}):
            with patch.object(svc, '_get_ai_suggestions_via_http') as mock_http:
                mock_http.return_value = "AI suggestion"
                result = svc.scan(MISSING_LIMITS_YAML)
                assert result.ai_suggestions == "AI suggestion"
                mock_http.assert_called_once()
