"""Tests for the AI Engine microservice endpoints (ai_engine/main.py)."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def ai_client():
    """Return a TestClient for the AI Engine FastAPI app."""
    with patch('ai_engine.diagnoser.AIDiagnoser') as MockDiagnoser:
        from ai_engine.main import app, _diagnoser
        # Reset the module-level singleton for test isolation
        import ai_engine.main
        ai_engine.main._diagnoser = None
        with TestClient(app) as c:
            yield c


@pytest.fixture
def mock_diagnoser():
    """Return a mock AIDiagnoser instance."""
    mock = MagicMock()
    mock.diagnose.return_value = {
        "root_cause": "Database connection timeout",
        "detailed_analysis": "The pod failed to connect to the database within the configured timeout period.",
        "remediation": "Check database connectivity and increase connection timeout.",
        "raw_analysis": "Full analysis text here...",
        "model_used": "openai/gpt-4o-mini",
    }
    mock.suggest.return_value = "This is a suggestion from the AI."
    return mock


class TestAIEngineHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self, ai_client):
        """GET /health should return status healthy with providers dict."""
        response = ai_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "providers" in data
        assert set(data["providers"].keys()) == {"ollama", "openai", "gemini"}


class TestAIEngineDiagnoseEndpoint:
    """Tests for the /diagnose endpoint."""

    def test_diagnose_returns_structured_response(self, ai_client, mock_diagnoser):
        """POST /diagnose should return structured diagnosis response."""
        import ai_engine.main
        ai_engine.main._diagnoser = mock_diagnoser

        response = ai_client.post("/diagnose", json={
            "pod_name": "test-pod",
            "namespace": "default",
            "describe": "Phase: CrashLoopBackOff\nEvents: Back-off restarting",
            "logs": "Error: connection refused to db:5432",
            "error_type": "CrashLoopBackOff",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["root_cause"] == "Database connection timeout"
        assert data["model_used"] == "openai/gpt-4o-mini"
        assert "remediation" in data

    def test_diagnose_handles_missing_optional_fields(self, ai_client, mock_diagnoser):
        """POST /diagnose should work with minimal required fields."""
        import ai_engine.main
        ai_engine.main._diagnoser = mock_diagnoser

        response = ai_client.post("/diagnose", json={
            "pod_name": "minimal-pod",
            "namespace": "kube-system",
            "describe": "Phase: Pending",
            "logs": "No logs available",
        })

        assert response.status_code == 200
        mock_diagnoser.diagnose.assert_called_once()

    def test_diagnose_missing_required_fields_returns_422(self, ai_client):
        """POST /diagnose with missing required fields should return 422."""
        response = ai_client.post("/diagnose", json={
            "pod_name": "test-pod",
            # Missing namespace, describe, logs
        })
        assert response.status_code == 422

    def test_diagnose_handles_none_detailed_analysis(self, ai_client):
        """POST /diagnose should handle null detailed_analysis."""
        mock = MagicMock()
        mock.diagnose.return_value = {
            "root_cause": "Unknown error",
            "detailed_analysis": None,
            "remediation": "Check logs",
            "raw_analysis": "Raw text",
            "model_used": "none",
        }
        import ai_engine.main
        ai_engine.main._diagnoser = mock

        response = ai_client.post("/diagnose", json={
            "pod_name": "test-pod",
            "namespace": "default",
            "describe": "Phase: Unknown",
            "logs": "No logs",
            "error_type": "Unknown",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["detailed_analysis"] is None


class TestAIEngineSuggestEndpoint:
    """Tests for the /suggest endpoint."""

    def test_suggest_returns_suggestion(self, ai_client, mock_diagnoser):
        """POST /suggest should return AI suggestion."""
        import ai_engine.main
        ai_engine.main._diagnoser = mock_diagnoser

        response = ai_client.post("/suggest", json={
            "prompt": "Explain Kubernetes readiness probes"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["suggestion"] == "This is a suggestion from the AI."

    def test_suggest_missing_prompt_returns_422(self, ai_client):
        """POST /suggest without prompt should return 422."""
        response = ai_client.post("/suggest", json={})
        assert response.status_code == 422


class TestGetDiagnoserSingleton:
    """Tests for the _get_diagnoser helper function."""

    def test_get_diagnoser_creates_singleton(self):
        """_get_diagnoser should create and cache a singleton AIDiagnoser."""
        import ai_engine.main
        ai_engine.main._diagnoser = None

        with patch('ai_engine.diagnoser.AIDiagnoser') as MockClass:
            mock_instance = MagicMock()
            MockClass.return_value = mock_instance

            # Call should create the singleton
            result1 = ai_engine.main._get_diagnoser()
            result2 = ai_engine.main._get_diagnoser()

            # Should only create once
            MockClass.assert_called_once()
            assert result1 is result2
