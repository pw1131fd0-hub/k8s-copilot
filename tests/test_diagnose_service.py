"""Tests for DiagnoseService - AI orchestration and HTTP/local calls."""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from backend.services.diagnose_service import DiagnoseService, _validate_ai_engine_url


class TestValidateAIEngineURL:
    """Tests for _validate_ai_engine_url helper."""

    def test_valid_http_url(self):
        """Should return sanitized URL for valid http URLs."""
        result = _validate_ai_engine_url("http://localhost:8001")
        assert result == "http://localhost:8001"

    def test_valid_https_url(self):
        """Should return sanitized URL for valid https URLs."""
        result = _validate_ai_engine_url("https://ai-engine.example.com/api")
        assert result == "https://ai-engine.example.com/api"

    def test_strips_trailing_slash(self):
        """Should strip trailing slashes from the URL."""
        result = _validate_ai_engine_url("http://localhost:8001/")
        assert result == "http://localhost:8001"

    def test_invalid_scheme_returns_none(self):
        """Should return None for non-http/https schemes."""
        result = _validate_ai_engine_url("ftp://localhost:21")
        assert result is None

    def test_empty_url_returns_none(self):
        """Should return None for empty string."""
        result = _validate_ai_engine_url("")
        assert result is None

    def test_no_host_returns_none(self):
        """Should return None for URLs without host."""
        result = _validate_ai_engine_url("http://")
        assert result is None

    def test_malformed_url_returns_none(self):
        """Should return None for completely malformed URLs."""
        result = _validate_ai_engine_url("not-a-valid-url")
        assert result is None


class TestDiagnoseServiceCallAIEngineService:
    """Tests for _call_ai_engine_service method (HTTP calls)."""

    def test_successful_http_call(self):
        """Should return structured AIResult on successful HTTP call."""
        import httpx
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "root_cause": "Database timeout",
            "detailed_analysis": "Connection pool exhausted",
            "remediation": "Increase pool size",
            "raw_analysis": "Full analysis",
            "model_used": "openai/gpt-4o-mini",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://localhost:8001'}):
            with patch('httpx.Client') as MockClient:
                mock_client = MagicMock()
                MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
                MockClient.return_value.__exit__ = MagicMock(return_value=False)
                mock_client.post.return_value = mock_response

                service = DiagnoseService()
                result = service._call_ai_engine_service({
                    "pod_name": "test-pod",
                    "namespace": "default",
                    "describe": "Phase: Failed",
                    "logs": "Error",
                    "error_type": "CrashLoopBackOff",
                })

        assert result["root_cause"] == "Database timeout"
        assert result["model_used"] == "openai/gpt-4o-mini"

    def test_timeout_returns_error_result(self):
        """Should return error AIResult on timeout."""
        import httpx

        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://localhost:8001'}):
            with patch('httpx.Client') as MockClient:
                mock_client = MagicMock()
                MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
                MockClient.return_value.__exit__ = MagicMock(return_value=False)
                mock_client.post.side_effect = httpx.TimeoutException("Read timeout")

                service = DiagnoseService()
                result = service._call_ai_engine_service({"pod_name": "test"})

        assert "timed out" in result["root_cause"]
        assert result["model_used"] == "error"

    def test_http_status_error_returns_error_result(self):
        """Should return error AIResult on HTTP status error."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://localhost:8001'}):
            with patch('httpx.Client') as MockClient:
                mock_client = MagicMock()
                MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
                MockClient.return_value.__exit__ = MagicMock(return_value=False)
                mock_client.post.return_value = mock_response
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Server error", request=MagicMock(), response=mock_response
                )

                service = DiagnoseService()
                result = service._call_ai_engine_service({"pod_name": "test"})

        assert "HTTP 500" in result["root_cause"]
        assert result["model_used"] == "error"

    def test_generic_exception_returns_error_result(self):
        """Should return error AIResult on unexpected exception."""
        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://localhost:8001'}):
            with patch('httpx.Client') as MockClient:
                mock_client = MagicMock()
                MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
                MockClient.return_value.__exit__ = MagicMock(return_value=False)
                mock_client.post.side_effect = Exception("Connection refused")

                service = DiagnoseService()
                result = service._call_ai_engine_service({"pod_name": "test"})

        assert "failed" in result["root_cause"].lower()
        assert result["model_used"] == "error"


class TestDiagnoseServiceCallAIEngineLocal:
    """Tests for _call_ai_engine_local method."""

    def test_local_call_returns_result(self):
        """Should call local AIDiagnoser and return AIResult."""
        mock_diagnoser_result = {
            "root_cause": "OOM killed",
            "detailed_analysis": "Memory limit exceeded",
            "remediation": "Increase memory limit",
            "raw_analysis": "Full analysis",
            "model_used": "ollama/llama3.2",
        }

        with patch('ai_engine.diagnoser.AIDiagnoser') as MockDiagnoser:
            mock_instance = MagicMock()
            mock_instance.diagnose.return_value = mock_diagnoser_result
            MockDiagnoser.return_value = mock_instance

            with patch.dict('os.environ', {}, clear=False):
                # Clear AI_ENGINE_URL so it uses local
                import os
                old_url = os.environ.pop('AI_ENGINE_URL', None)
                try:
                    service = DiagnoseService()
                    result = service._call_ai_engine_local({
                        "pod_name": "test-pod",
                        "namespace": "default",
                        "describe": "Phase: Failed",
                        "logs": "Error",
                        "error_type": "OOMKilled",
                    })
                finally:
                    if old_url:
                        os.environ['AI_ENGINE_URL'] = old_url

        assert result["root_cause"] == "OOM killed"
        assert result["model_used"] == "ollama/llama3.2"


class TestDiagnoseServiceDiagnose:
    """Tests for the main diagnose method."""

    @pytest.fixture
    def mock_db(self):
        """Return a mock SQLAlchemy session."""
        mock = MagicMock(spec=Session)
        return mock

    @pytest.fixture
    def mock_pod_service(self):
        """Return a mock PodService."""
        mock = MagicMock()
        mock.get_pod_context.return_value = {
            "pod_name": "test-pod",
            "namespace": "default",
            "describe": "Phase: CrashLoopBackOff",
            "logs": "Error connecting to database",
            "error_type": "CrashLoopBackOff",
        }
        return mock

    def test_diagnose_uses_http_when_ai_engine_url_set(self, mock_db, mock_pod_service):
        """Should use HTTP service when AI_ENGINE_URL is configured."""
        import httpx

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "root_cause": "DB connection issue",
            "detailed_analysis": None,
            "remediation": "Check DB credentials",
            "raw_analysis": "Analysis",
            "model_used": "openai/gpt-4o",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict('os.environ', {'AI_ENGINE_URL': 'http://ai-engine:8001'}):
            with patch('httpx.Client') as MockClient:
                mock_client = MagicMock()
                MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
                MockClient.return_value.__exit__ = MagicMock(return_value=False)
                mock_client.post.return_value = mock_response

                service = DiagnoseService()
                service._pod_service = mock_pod_service

                result = service.diagnose("test-pod", "default", mock_db)

        assert result.root_cause == "DB connection issue"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_diagnose_uses_local_when_no_ai_engine_url(self, mock_db, mock_pod_service):
        """Should use local AIDiagnoser when AI_ENGINE_URL is not set."""
        mock_diagnoser_result = {
            "root_cause": "Config error",
            "detailed_analysis": "Missing env var",
            "remediation": "Set DATABASE_URL",
            "raw_analysis": "Analysis",
            "model_used": "ollama/llama3.2",
        }

        with patch('ai_engine.diagnoser.AIDiagnoser') as MockDiagnoser:
            mock_instance = MagicMock()
            mock_instance.diagnose.return_value = mock_diagnoser_result
            MockDiagnoser.return_value = mock_instance

            import os
            old_url = os.environ.pop('AI_ENGINE_URL', None)
            try:
                service = DiagnoseService()
                service._pod_service = mock_pod_service
                result = service.diagnose("test-pod", "default", mock_db)
            finally:
                if old_url:
                    os.environ['AI_ENGINE_URL'] = old_url

        assert result.root_cause == "Config error"

    def test_diagnose_handles_db_error_gracefully(self, mock_db, mock_pod_service):
        """Should still return result even if DB commit fails."""
        mock_db.commit.side_effect = Exception("DB connection lost")

        mock_diagnoser_result = {
            "root_cause": "Test error",
            "detailed_analysis": None,
            "remediation": "Fix it",
            "raw_analysis": "Raw",
            "model_used": "test",
        }

        with patch('ai_engine.diagnoser.AIDiagnoser') as MockDiagnoser:
            mock_instance = MagicMock()
            mock_instance.diagnose.return_value = mock_diagnoser_result
            MockDiagnoser.return_value = mock_instance

            import os
            old_url = os.environ.pop('AI_ENGINE_URL', None)
            try:
                service = DiagnoseService()
                service._pod_service = mock_pod_service
                result = service.diagnose("test-pod", "default", mock_db)
            finally:
                if old_url:
                    os.environ['AI_ENGINE_URL'] = old_url

        # Should still return result
        assert result.root_cause == "Test error"
        # Should have rolled back
        mock_db.rollback.assert_called_once()
