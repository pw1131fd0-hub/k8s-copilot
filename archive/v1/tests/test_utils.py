"""Tests for backend utility functions and helpers."""
from backend.utils import mask_sensitive_data, is_secret_resource, K8S_NAME_RE, PodNotFoundError


class TestMaskSensitiveData:
    """Tests for the mask_sensitive_data utility function."""

    def test_masks_password(self):
        """Password values should be replaced with [MASKED]."""
        text = 'password: supersecret123'
        result = mask_sensitive_data(text)
        assert 'supersecret123' not in result
        assert '[MASKED]' in result

    def test_masks_token(self):
        """Token values should be redacted."""
        text = 'token=eyJhbGciOiJSUzI1NiJ9.payload'
        result = mask_sensitive_data(text)
        assert 'eyJhbGciOiJSUzI1NiJ9' not in result

    def test_masks_api_key(self):
        """API key values should be redacted."""
        text = 'api_key: sk-abc123xyz'
        result = mask_sensitive_data(text)
        assert 'sk-abc123xyz' not in result

    def test_masks_bearer_token(self):
        """Bearer token values should be redacted."""
        text = 'Authorization: Bearer eyJhbGciOiJSUzI1NiJ9longtokenvalue'
        result = mask_sensitive_data(text)
        assert 'eyJhbGciOiJSUzI1NiJ9longtokenvalue' not in result

    def test_masks_database_url_password(self):
        """Database URLs with embedded passwords should have the password redacted."""
        text = 'postgres://myuser:supersecretpassword@db-host:5432/mydb'
        result = mask_sensitive_data(text)
        assert 'supersecretpassword' not in result
        assert '[MASKED]' in result

    def test_masks_aws_access_key_id(self):
        """AWS access key IDs (AKIA...) should be redacted."""
        text = 'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE'
        result = mask_sensitive_data(text)
        assert 'AKIAIOSFODNN7EXAMPLE' not in result

    def test_masks_json_inline_secret(self):
        """JSON-style inline secrets like "password":"value" should be redacted."""
        text = '{"password":"hunter2","user":"admin"}'
        result = mask_sensitive_data(text)
        assert 'hunter2' not in result

    def test_preserves_non_sensitive(self):
        """Non-sensitive text should be returned unchanged."""
        text = 'Hello World, this is a normal message'
        result = mask_sensitive_data(text)
        assert result == text

    def test_empty_string(self):
        """Empty string should be returned as-is."""
        assert mask_sensitive_data('') == ''


class TestIsSecretResource:
    """Tests for the is_secret_resource utility function."""

    def test_secret_kind(self):
        """Dict with kind 'Secret' should be identified as a secret resource."""
        assert is_secret_resource({'kind': 'Secret'}) is True

    def test_secret_kind_lowercase(self):
        """Dict with kind 'secret' (lowercase) should also be identified as a secret resource."""
        assert is_secret_resource({'kind': 'secret'}) is True

    def test_deployment_kind(self):
        """Dict with kind 'Deployment' should not be identified as a secret resource."""
        assert is_secret_resource({'kind': 'Deployment'}) is False

    def test_empty_dict(self):
        """Empty dict should not be identified as a secret resource."""
        assert is_secret_resource({}) is False


class TestK8sNameRe:
    """Tests for the Kubernetes DNS-subdomain name validation regex."""

    def test_valid_simple_name(self):
        """Simple lowercase hyphenated name should match."""
        assert K8S_NAME_RE.match('my-pod') is not None

    def test_valid_alphanumeric(self):
        """Alphanumeric name should match."""
        assert K8S_NAME_RE.match('pod123') is not None

    def test_valid_single_char(self):
        """Single lowercase character should match."""
        assert K8S_NAME_RE.match('a') is not None

    def test_valid_with_hyphens(self):
        """Name with multiple hyphens should match."""
        assert K8S_NAME_RE.match('my-app-v2-deployment') is not None

    def test_invalid_uppercase(self):
        """Name with uppercase letters should not match."""
        assert K8S_NAME_RE.match('MyPod') is None

    def test_invalid_starts_with_hyphen(self):
        """Name starting with a hyphen should not match."""
        assert K8S_NAME_RE.match('-bad-name') is None

    def test_invalid_ends_with_hyphen(self):
        """Name ending with a hyphen should not match."""
        assert K8S_NAME_RE.match('bad-name-') is None

    def test_invalid_underscore(self):
        """Name containing an underscore should not match."""
        assert K8S_NAME_RE.match('bad_name') is None

    def test_invalid_empty_string(self):
        """Empty string should not match."""
        assert K8S_NAME_RE.match('') is None

    def test_invalid_dot(self):
        """Name containing a dot should not match."""
        assert K8S_NAME_RE.match('bad.name') is None


class TestPodNotFoundError:
    """Tests for the PodNotFoundError custom exception."""

    def test_error_message_contains_pod_name(self):
        """Exception message should include the pod name."""
        err = PodNotFoundError('my-pod', 'default')
        assert 'my-pod' in str(err)

    def test_error_message_contains_namespace(self):
        """Exception message should include the namespace."""
        err = PodNotFoundError('my-pod', 'production')
        assert 'production' in str(err)

    def test_stores_pod_name_attribute(self):
        """Exception should store the pod name as an attribute."""
        err = PodNotFoundError('crash-pod', 'staging')
        assert err.pod_name == 'crash-pod'

    def test_stores_namespace_attribute(self):
        """Exception should store the namespace as an attribute."""
        err = PodNotFoundError('crash-pod', 'staging')
        assert err.namespace == 'staging'

    def test_is_exception(self):
        """PodNotFoundError should be a subclass of Exception."""
        err = PodNotFoundError('pod', 'ns')
        assert isinstance(err, Exception)
