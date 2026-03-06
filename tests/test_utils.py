import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from backend.utils import mask_sensitive_data, is_secret_resource


class TestMaskSensitiveData:
    def test_masks_password(self):
        text = 'password: supersecret123'
        result = mask_sensitive_data(text)
        assert 'supersecret123' not in result
        assert '[MASKED]' in result

    def test_masks_token(self):
        text = 'token=eyJhbGciOiJSUzI1NiJ9.payload'
        result = mask_sensitive_data(text)
        assert 'eyJhbGciOiJSUzI1NiJ9' not in result

    def test_masks_api_key(self):
        text = 'api_key: sk-abc123xyz'
        result = mask_sensitive_data(text)
        assert 'sk-abc123xyz' not in result

    def test_masks_bearer_token(self):
        text = 'Authorization: Bearer eyJhbGciOiJSUzI1NiJ9longtokenvalue'
        result = mask_sensitive_data(text)
        assert 'eyJhbGciOiJSUzI1NiJ9longtokenvalue' not in result

    def test_preserves_non_sensitive(self):
        text = 'Hello World, this is a normal message'
        result = mask_sensitive_data(text)
        assert result == text

    def test_empty_string(self):
        assert mask_sensitive_data('') == ''


class TestIsSecretResource:
    def test_secret_kind(self):
        assert is_secret_resource({'kind': 'Secret'}) is True

    def test_secret_kind_lowercase(self):
        assert is_secret_resource({'kind': 'secret'}) is True

    def test_deployment_kind(self):
        assert is_secret_resource({'kind': 'Deployment'}) is False

    def test_empty_dict(self):
        assert is_secret_resource({}) is False
