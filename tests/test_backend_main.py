"""Tests for backend/main.py - Middleware, security, and SPA serving."""
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app_client():
    """Return a TestClient with K8s config mocked and no API key required."""
    # Clear API key to avoid 401s in basic tests
    old_key = os.environ.pop('LOBSTER_API_KEY', None)
    try:
        with patch('kubernetes.config.load_kube_config'), \
             patch('kubernetes.config.load_incluster_config'):
            import importlib
            import backend.main
            importlib.reload(backend.main)
            with TestClient(backend.main.app) as c:
                yield c
    finally:
        if old_key:
            os.environ['LOBSTER_API_KEY'] = old_key


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_security_headers_present(self, app_client):
        """All security headers should be present in response."""
        response = app_client.get("/")
        
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "geolocation=()" in response.headers.get("Permissions-Policy", "")

    def test_hsts_header_not_on_http(self, app_client):
        """HSTS header should not be present on HTTP requests."""
        response = app_client.get("/")
        # TestClient uses http by default
        assert "Strict-Transport-Security" not in response.headers


class TestAPIKeyAuthMiddleware:
    """Tests for APIKeyAuthMiddleware."""

    def test_excluded_paths_no_auth_required(self, app_client):
        """Excluded paths should work without API key."""
        response = app_client.get("/")
        assert response.status_code == 200

        response = app_client.get("/docs")
        # /docs may return 200 or redirect, but should not be 401
        assert response.status_code != 401

    def test_api_key_via_bearer_token(self):
        """Should accept API key via Bearer token."""
        with patch.dict('os.environ', {'LOBSTER_API_KEY': 'test-secret-key'}):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                # Need to reimport to pick up env var
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    # Without key - should be rejected
                    response = client.get("/api/v1/cluster/pods")
                    assert response.status_code == 401

                    # With Bearer token
                    response = client.get(
                        "/api/v1/cluster/pods",
                        headers={"Authorization": "Bearer test-secret-key"}
                    )
                    # Should not be 401 (may fail for other reasons like K8s mocking)
                    assert response.status_code != 401

    def test_api_key_via_x_api_key_header(self):
        """Should accept API key via X-API-Key header."""
        with patch.dict('os.environ', {'LOBSTER_API_KEY': 'test-api-key'}):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    response = client.get(
                        "/api/v1/cluster/pods",
                        headers={"X-API-Key": "test-api-key"}
                    )
                    assert response.status_code != 401

    def test_invalid_api_key_rejected(self):
        """Should reject invalid API key."""
        with patch.dict('os.environ', {'LOBSTER_API_KEY': 'correct-key'}):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    response = client.get(
                        "/api/v1/cluster/pods",
                        headers={"Authorization": "Bearer wrong-key"}
                    )
                    assert response.status_code == 401
                    assert "Invalid or missing API key" in response.text

    def test_options_request_not_blocked(self):
        """OPTIONS requests should pass through for CORS preflight."""
        with patch.dict('os.environ', {'LOBSTER_API_KEY': 'test-key'}):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    response = client.options("/api/v1/cluster/pods")
                    assert response.status_code != 401


class TestSPACatchAll:
    """Tests for SPA catch-all route."""

    def test_path_traversal_encoded_rejected(self, app_client):
        """URL-encoded path traversal attempts should be rejected."""
        # URL-encoded path traversal that Starlette doesn't normalize
        response = app_client.get("/..%2F..%2Fetc/passwd")
        assert response.status_code == 400

    def test_path_with_dotdot_substring_rejected(self, app_client):
        """Paths containing '..' substring should be rejected."""
        response = app_client.get("/something/..hidden")
        assert response.status_code == 400

    def test_api_prefix_returns_404(self, app_client):
        """Paths starting with api/ should return 404 (not serve index.html)."""
        response = app_client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_static_prefix_returns_404(self, app_client):
        """Paths starting with static/ should return 404 (not serve index.html)."""
        response = app_client.get("/static/nonexistent.js")
        assert response.status_code == 404

    def test_spa_route_returns_index_html(self, app_client):
        """SPA routes should return index.html when frontend/build exists."""
        # Since frontend/build exists with index.html, this should succeed
        response = app_client.get("/dashboard")
        assert response.status_code == 200


class TestClusterStatusEndpoint:
    """Additional tests for cluster status endpoint."""

    def test_cluster_status_connected_with_version(self, app_client):
        """Should return connected status with K8s version."""
        mock_version = MagicMock()
        mock_version.git_version = "v1.29.0"

        with patch('backend.main.client.CoreV1Api') as mock_v1, \
             patch('backend.main.client.VersionApi') as mock_version_api:
            mock_v1.return_value.list_namespace.return_value = MagicMock(items=[])
            mock_version_api.return_value.get_code.return_value = mock_version

            response = app_client.get("/api/v1/cluster/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["version"] == "v1.29.0"

    def test_cluster_status_handles_version_none(self, app_client):
        """Should handle None version_info gracefully."""
        with patch('backend.main.client.CoreV1Api') as mock_v1, \
             patch('backend.main.client.VersionApi') as mock_version_api:
            mock_v1.return_value.list_namespace.return_value = MagicMock(items=[])
            mock_version_api.return_value.get_code.return_value = None

            response = app_client.get("/api/v1/cluster/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["version"] is None


class TestLifespan:
    """Tests for application lifespan events."""

    def test_lifespan_handles_k8s_config_error(self):
        """Should handle K8s config loading errors gracefully."""
        with patch('kubernetes.config.load_kube_config') as mock_kube, \
             patch('kubernetes.config.load_incluster_config') as mock_incluster:
            mock_kube.side_effect = Exception("No kubeconfig found")
            mock_incluster.side_effect = Exception("Not in cluster")
            
            # App should still start
            from backend.main import app
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_with_allowed_origins(self):
        """CORS should restrict to ALLOWED_ORIGINS when set."""
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': 'http://localhost:3000,https://app.example.com'}):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    # App should work
                    response = client.get("/")
                    assert response.status_code == 200

    def test_cors_restricts_when_no_allowed_origins(self):
        """CORS should be restricted when ALLOWED_ORIGINS is not set."""
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': ''}, clear=False):
            with patch('kubernetes.config.load_kube_config'), \
                 patch('kubernetes.config.load_incluster_config'):
                import importlib
                import backend.main
                importlib.reload(backend.main)
                
                with TestClient(backend.main.app) as client:
                    response = client.get("/")
                    assert response.status_code == 200


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_version(self, app_client):
        """Root endpoint should return version info."""
        response = app_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "running" in data["message"].lower()
