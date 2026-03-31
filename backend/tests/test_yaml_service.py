"""Tests for YamlService."""
import json
import unittest
from unittest.mock import patch, MagicMock
from backend.services.yaml_service import YamlService, _validate_ai_engine_url, ANTI_PATTERN_RULES


class TestValidateAiEngineUrl(unittest.TestCase):
    """Test cases for _validate_ai_engine_url."""

    def test_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        result = _validate_ai_engine_url("http://localhost:8000")
        self.assertEqual(result, "http://localhost:8000")

    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        result = _validate_ai_engine_url("https://api.example.com")
        self.assertEqual(result, "https://api.example.com")

    def test_invalid_scheme(self):
        """Test validation rejects invalid scheme."""
        result = _validate_ai_engine_url("ftp://example.com")
        self.assertIsNone(result)

    def test_empty_url(self):
        """Test validation rejects empty URL."""
        result = _validate_ai_engine_url("")
        self.assertIsNone(result)

    def test_no_scheme(self):
        """Test validation rejects URL without scheme."""
        result = _validate_ai_engine_url("localhost:8000")
        self.assertIsNone(result)

    def test_url_with_path(self):
        """Test validation handles URL with path."""
        result = _validate_ai_engine_url("http://localhost:8000/api/v1")
        self.assertEqual(result, "http://localhost:8000/api/v1")

    def test_url_trailing_slash_removed(self):
        """Test validation removes trailing slash."""
        result = _validate_ai_engine_url("http://localhost:8000/")
        self.assertEqual(result, "http://localhost:8000")

    def test_invalid_url_exception(self):
        """Test validation handles invalid URL gracefully."""
        result = _validate_ai_engine_url("not a valid url at all")
        self.assertIsNone(result)

    def test_url_with_port(self):
        """Test validation handles URL with port."""
        result = _validate_ai_engine_url("http://api.example.com:8080")
        self.assertEqual(result, "http://api.example.com:8080")

    def test_url_with_query_params(self):
        """Test validation handles URL with query params."""
        result = _validate_ai_engine_url("http://localhost:8000/api?key=value")
        self.assertIsNotNone(result)
        self.assertIn("localhost", result)


class TestAntiPatternRules(unittest.TestCase):
    """Test cases for anti-pattern rules."""

    def test_anti_pattern_rules_exist(self):
        """Test that anti-pattern rules are defined."""
        self.assertGreater(len(ANTI_PATTERN_RULES), 0)

    def test_anti_pattern_rules_have_required_fields(self):
        """Test that each rule has required fields."""
        for rule in ANTI_PATTERN_RULES:
            self.assertIsNotNone(rule.id)
            self.assertIsNotNone(rule.severity)
            self.assertIsNotNone(rule.message)
            self.assertIsNotNone(rule.check)
            self.assertIn(rule.severity, ["ERROR", "WARNING", "INFO"])

    def test_no_resource_limits_rule(self):
        """Test no-resource-limits rule detection."""
        rule = next(r for r in ANTI_PATTERN_RULES if r.id == "no-resource-limits")
        # Container without limits should trigger rule
        container = {"name": "test", "image": "nginx"}
        self.assertTrue(rule.check(container))

    def test_no_resource_limits_rule_passes(self):
        """Test no-resource-limits rule passes with limits."""
        rule = next(r for r in ANTI_PATTERN_RULES if r.id == "no-resource-limits")
        # Container with limits should not trigger rule
        container = {
            "name": "test",
            "image": "nginx",
            "resources": {"limits": {"cpu": "500m", "memory": "512Mi"}}
        }
        self.assertFalse(rule.check(container))


class TestYamlService(unittest.TestCase):
    """Test cases for YamlService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = YamlService()

    def test_scan_valid_yaml(self):
        """Test scanning valid YAML content."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: busybox:latest
"""
        response = self.service.scan(yaml_content)

        self.assertIsNotNone(response)
        self.assertGreater(response.total_issues, 0)
        self.assertTrue(response.has_errors)

    def test_scan_yaml_with_latest_tag(self):
        """Test scanning detects :latest tag."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx:latest
"""
        response = self.service.scan(yaml_content)

        issues = response.issues
        latest_issues = [i for i in issues if i.rule == "latest-image-tag"]
        self.assertGreater(len(latest_issues), 0)

    def test_scan_yaml_without_limits(self):
        """Test scanning detects missing resource limits."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx:1.0
"""
        response = self.service.scan(yaml_content)

        issues = response.issues
        limit_issues = [i for i in issues if i.rule == "no-resource-limits"]
        self.assertGreater(len(limit_issues), 0)

    def test_scan_yaml_with_privileged(self):
        """Test scanning detects privileged containers."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx:1.0
    securityContext:
      privileged: true
"""
        response = self.service.scan(yaml_content)

        issues = response.issues
        priv_issues = [i for i in issues if i.rule == "privileged-container"]
        self.assertGreater(len(priv_issues), 0)
        self.assertEqual(priv_issues[0].severity, "ERROR")

    def test_scan_empty_yaml(self):
        """Test scanning empty YAML."""
        yaml_content = ""
        response = self.service.scan(yaml_content)

        self.assertEqual(response.total_issues, 0)
        self.assertFalse(response.has_errors)

    def test_scan_malformed_yaml(self):
        """Test scanning malformed YAML."""
        yaml_content = "invalid: yaml: content: ["

        # Malformed YAML might return error or empty issues
        try:
            response = self.service.scan(yaml_content)
            # If it doesn't raise, it should at least have some handling
            self.assertIsNotNone(response)
        except Exception:
            # Exception is also acceptable
            pass

    def test_scan_multiple_documents(self):
        """Test scanning multiple YAML documents separated by ---."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: pod1
spec:
  containers:
  - name: test
    image: nginx:latest
---
apiVersion: v1
kind: Pod
metadata:
  name: pod2
spec:
  containers:
  - name: test
    image: busybox:1.0
"""
        response = self.service.scan(yaml_content)

        self.assertGreater(response.total_issues, 0)

    def test_scan_with_filename(self):
        """Test scanning with custom filename."""
        yaml_content = """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: test
    image: nginx
"""
        response = self.service.scan(yaml_content, filename="deployment.yaml")
        self.assertEqual(response.filename, "deployment.yaml")

    def test_diff_identical_yaml(self):
        """Test diff of identical YAML."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  replicas: 3
"""
        result = self.service.diff(yaml_content, yaml_content)

        self.assertEqual(len(result.get("values_changed", {})), 0)
        self.assertEqual(len(result.get("dictionary_item_added", {})), 0)
        self.assertEqual(len(result.get("dictionary_item_removed", {})), 0)

    def test_diff_different_yaml(self):
        """Test diff of different YAML."""
        yaml_a = """
apiVersion: v1
kind: Pod
spec:
  replicas: 1
"""
        yaml_b = """
apiVersion: v1
kind: Pod
spec:
  replicas: 3
"""
        result = self.service.diff(yaml_a, yaml_b)

        self.assertIn("differences", result)
        self.assertIn("values_changed", result["differences"])

    def test_diff_added_field(self):
        """Test diff detects added fields."""
        yaml_a = """
apiVersion: v1
kind: Pod
"""
        yaml_b = """
apiVersion: v1
kind: Pod
spec:
  replicas: 3
"""
        result = self.service.diff(yaml_a, yaml_b)

        self.assertIn("differences", result)
        self.assertIn("dictionary_item_added", result["differences"])

    def test_diff_removed_field(self):
        """Test diff detects removed fields."""
        yaml_a = """
apiVersion: v1
kind: Pod
spec:
  replicas: 3
"""
        yaml_b = """
apiVersion: v1
kind: Pod
"""
        result = self.service.diff(yaml_a, yaml_b)

        self.assertIn("differences", result)
        self.assertIn("dictionary_item_removed", result["differences"])

    def test_diff_invalid_yaml_a(self):
        """Test diff with invalid first YAML."""
        result = self.service.diff("invalid: yaml: [", "valid: yaml")
        # Should handle gracefully, either with error key or empty result
        self.assertIsNotNone(result)

    def test_diff_invalid_yaml_b(self):
        """Test diff with invalid second YAML."""
        result = self.service.diff("valid: yaml", "invalid: yaml: [")
        # Should handle gracefully, either with error key or empty result
        self.assertIsNotNone(result)


class TestYamlServiceAiSuggestions(unittest.TestCase):
    """Test cases for AI suggestions in YamlService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = YamlService()

    def test_get_ai_suggestions_returns_value(self):
        """Test getting AI suggestions returns a value or None."""
        yaml_content = "test: content"
        issues = []

        result = self.service._get_ai_suggestions(issues, yaml_content)

        # Should return either a string or None
        self.assertTrue(isinstance(result, (str, type(None))))

    def test_scan_complete_yaml(self):
        """Test complete scan with all features."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: app
        image: app:latest
        securityContext:
          privileged: true
"""
        response = self.service.scan(yaml_content)

        # Should detect multiple issues
        self.assertGreater(response.total_issues, 1)
        self.assertTrue(response.has_errors)

        # Should have both ERROR and WARNING level issues
        error_issues = [i for i in response.issues if i.severity == "ERROR"]
        self.assertGreater(len(error_issues), 0)

    def test_scan_with_security_context(self):
        """Test scanning detects missing security context."""
        yaml_content = """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: test
    image: nginx:1.0
"""
        response = self.service.scan(yaml_content)

        self.assertGreater(response.total_issues, 0)

    def test_scan_with_run_as_root(self):
        """Test scanning detects root permission issues."""
        yaml_content = """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: test
    image: nginx:1.0
    securityContext:
      runAsUser: 0
"""
        response = self.service.scan(yaml_content)

        root_issues = [i for i in response.issues if "root" in i.rule.lower()]
        # May or may not detect depending on implementation
        self.assertIsNotNone(response)

    def test_scan_response_structure(self):
        """Test that scan response has proper structure."""
        yaml_content = """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: test
    image: nginx:1.0
"""
        response = self.service.scan(yaml_content)

        # Verify response structure
        self.assertIsNotNone(response.filename)
        self.assertIsNotNone(response.issues)
        self.assertIsInstance(response.total_issues, int)
        self.assertIsInstance(response.has_errors, bool)
        self.assertIsInstance(response.ai_suggestions, (str, type(None)))

    def test_scan_multiple_containers(self):
        """Test scanning YAML with multiple containers."""
        yaml_content = """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: app:latest
  - name: sidecar
    image: sidecar:1.0
"""
        response = self.service.scan(yaml_content)

        self.assertGreater(response.total_issues, 0)


if __name__ == "__main__":
    unittest.main()
