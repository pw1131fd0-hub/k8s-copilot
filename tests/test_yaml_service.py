"""Tests for the YAML scanning and diffing service."""
# pylint: disable=redefined-outer-name
import pytest

from backend.services.yaml_service import YamlService


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
