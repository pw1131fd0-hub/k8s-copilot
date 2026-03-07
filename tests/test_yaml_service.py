import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from backend.services.yaml_service import YamlService


@pytest.fixture
def svc():
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
    def test_valid_yaml_no_errors(self, svc):
        result = svc.scan(VALID_DEPLOYMENT)
        errors = [i for i in result.issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_missing_limits_detected(self, svc):
        result = svc.scan(MISSING_LIMITS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert result.has_errors is True

    def test_latest_tag_detected(self, svc):
        result = svc.scan(MISSING_LIMITS_YAML)
        rules = [i.rule for i in result.issues]
        assert 'latest-image-tag' in rules

    def test_privileged_container_detected(self, svc):
        result = svc.scan(PRIVILEGED_YAML)
        rules = [i.rule for i in result.issues]
        assert 'privileged-container' in rules

    def test_invalid_yaml_returns_error(self, svc):
        result = svc.scan(INVALID_YAML)
        assert result.has_errors is True
        assert result.issues[0].rule == 'yaml-parse-error'

    def test_scan_returns_correct_filename(self, svc):
        result = svc.scan(VALID_DEPLOYMENT, filename='myfile.yaml')
        assert result.filename == 'myfile.yaml'

    def test_total_issues_count(self, svc):
        result = svc.scan(MISSING_LIMITS_YAML)
        assert result.total_issues == len(result.issues)


class TestYamlServiceDiff:
    def test_diff_identical_yamls(self, svc):
        y = "foo: bar\nbaz: 1"
        assert svc.diff(y, y) == {}

    def test_diff_detects_changes(self, svc):
        a = "foo: bar"
        b = "foo: baz"
        result = svc.diff(a, b)
        assert result != {}

    def test_diff_handles_invalid_yaml(self, svc):
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


class TestYamlServiceJobKind:
    def test_job_containers_are_scanned(self, svc):
        result = svc.scan(JOB_YAML)
        rules = [i.rule for i in result.issues]
        assert 'no-resource-limits' in rules
        assert 'latest-image-tag' in rules

    def test_job_issues_flagged_as_errors(self, svc):
        result = svc.scan(JOB_YAML)
        assert result.has_errors is True
