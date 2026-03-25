"""Tests for the OllamaAnalyzer class."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from ai_engine.analyzers.ollama_analyzer import OllamaAnalyzer


class TestOllamaAnalyzerInit:
    """Tests for OllamaAnalyzer initialization."""

    def test_default_base_url(self):
        """Default base URL should be localhost:11434."""
        with patch.dict('os.environ', {}, clear=True):
            analyzer = OllamaAnalyzer()
            assert analyzer._base_url == "http://localhost:11434"

    def test_custom_base_url(self):
        """Custom base URL from env should be used."""
        with patch.dict('os.environ', {'OLLAMA_BASE_URL': 'http://ollama:11434'}):
            analyzer = OllamaAnalyzer()
            assert analyzer._base_url == "http://ollama:11434"

    def test_default_model(self):
        """Default model should be llama3."""
        with patch.dict('os.environ', {}, clear=True):
            analyzer = OllamaAnalyzer()
            assert analyzer._model == "llama3"

    def test_custom_model(self):
        """Custom model from env should be used."""
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'codellama'}):
            analyzer = OllamaAnalyzer()
            assert analyzer._model == "codellama"


class TestOllamaAnalyzerModelName:
    """Tests for the model_name property."""

    def test_model_name_format(self):
        """Model name should be formatted as ollama/<model>."""
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'llama3'}):
            analyzer = OllamaAnalyzer()
            assert analyzer.model_name == "ollama/llama3"


class TestOllamaAnalyzerIsAvailable:
    """Tests for the is_available method."""

    def test_is_available_success(self):
        """is_available should return True when Ollama responds with 200."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            assert analyzer.is_available() is True

    def test_is_available_non_200(self):
        """is_available should return False when Ollama returns non-200."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            assert analyzer.is_available() is False

    def test_is_available_connection_error(self):
        """is_available should return False on connection error."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            assert analyzer.is_available() is False

    def test_is_available_timeout(self):
        """is_available should return False on timeout."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            assert analyzer.is_available() is False


class TestOllamaAnalyzerAnalyze:
    """Tests for the analyze method."""

    def test_analyze_success(self):
        """analyze should return response text on success."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "This is the AI response"}
            mock_post.return_value = mock_response
            result = analyzer.analyze("Test prompt")
            assert result == "This is the AI response"

    def test_analyze_empty_response(self):
        """analyze should return empty string when response key is missing."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_post.return_value = mock_response
            result = analyzer.analyze("Test prompt")
            assert result == ""

    def test_analyze_http_error(self):
        """analyze should raise RuntimeError on HTTP error."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            mock_post.return_value = mock_response
            with pytest.raises(RuntimeError) as exc_info:
                analyzer.analyze("Test prompt")
            assert "HTTP 500" in str(exc_info.value)

    def test_analyze_request_error(self):
        """analyze should raise RuntimeError on request error."""
        analyzer = OllamaAnalyzer()
        with patch('httpx.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            with pytest.raises(RuntimeError) as exc_info:
                analyzer.analyze("Test prompt")
            assert "request failed" in str(exc_info.value)

    def test_analyze_sends_correct_payload(self):
        """analyze should send correct payload to Ollama."""
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'mistral'}):
            analyzer = OllamaAnalyzer()
            with patch('httpx.post') as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"response": "OK"}
                mock_post.return_value = mock_response

                analyzer.analyze("My test prompt")

                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert call_args[1]["json"]["model"] == "mistral"
                assert call_args[1]["json"]["prompt"] == "My test prompt"
                assert call_args[1]["json"]["stream"] is False
