"""Tests for the AIDiagnoser class and AI provider routing logic."""
import os
from unittest.mock import MagicMock, patch

import pytest

from ai_engine.diagnoser import AIDiagnoser


SAMPLE_CONTEXT = {
    "pod_name": "test-pod",
    "namespace": "default",
    "error_type": "CrashLoopBackOff",
    "describe": "Phase: Failed\nEvents:\nBackOff: Back-off restarting failed container",
    "logs": "Error: cannot connect to database at db:5432",
}


class TestAIDiagnoserNoProvider:
    """Tests for AIDiagnoser behaviour when no LLM provider is configured."""

    def test_returns_structured_dict_without_provider(self):
        """Should return a graceful fallback when no LLM is configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove all API keys to simulate no-provider
            env_patch = {k: '' for k in ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'OLLAMA_BASE_URL']}
            with patch.dict(os.environ, env_patch):
                diagnoser = AIDiagnoser()
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        assert 'root_cause' in result
        assert 'remediation' in result
        assert 'raw_analysis' in result
        assert 'model_used' in result

    def test_ollama_tmp_file_does_not_trigger_provider(self):
        """Presence of /tmp/ollama_available file must NOT trigger Ollama selection."""
        env_patch = {'OPENAI_API_KEY': '', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env_patch):
            with patch('os.path.exists', return_value=True):
                diagnoser = AIDiagnoser()
                diagnoser._analyzer = None  # pylint: disable=protected-access
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        # Without OLLAMA_BASE_URL the file should be irrelevant – fallback stub expected
        assert 'root_cause' in result
        assert result['model_used'] in ('none', 'error')


class TestAIDiagnoserWithMock:
    """Tests for AIDiagnoser with mocked LLM providers."""

    def test_uses_openai_when_configured(self):
        """Should call OpenAI and parse structured JSON when OPENAI_API_KEY is set."""
        mock_response = (
            '{"root_cause": "DB connection refused", "remediation": "kubectl exec..."}'
        )
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.openai_analyzer.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = MagicMock(
                    choices=[MagicMock(message=MagicMock(content=mock_response))]
                )
                diagnoser = AIDiagnoser()
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        assert result['root_cause'] == 'DB connection refused'
        assert 'kubectl exec' in result['remediation']
        assert result['model_used'].startswith('openai/')

    def test_openai_api_error_returns_fallback(self):
        """When OpenAI raises an exception, diagnose() should return an error stub."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.openai_analyzer.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
                diagnoser = AIDiagnoser()
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        assert 'root_cause' in result
        assert result['model_used'] == 'error'

    def test_gemini_api_error_returns_fallback(self):
        """When Gemini raises an exception, diagnose() should return an error stub."""
        env = {'OPENAI_API_KEY': '', 'GEMINI_API_KEY': 'test-key', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.gemini_analyzer.genai') as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API quota exceeded")
                diagnoser = AIDiagnoser()
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        assert 'root_cause' in result
        assert result['model_used'] == 'error'

    def test_parse_response_handles_malformed_json(self):
        """_parse_response should return a valid dict even when the LLM returns non-JSON."""
        diagnoser = AIDiagnoser()
        result = diagnoser._parse_response(  # pylint: disable=protected-access
            "Not valid JSON but contains useful info"
        )
        assert 'root_cause' in result
        assert 'remediation' in result

    def test_parse_response_extracts_json_from_markdown(self):
        """_parse_response should unwrap JSON fenced in markdown code blocks."""
        diagnoser = AIDiagnoser()
        raw = '```json\n{"root_cause": "OOM", "remediation": "Increase limits"}\n```'
        result = diagnoser._parse_response(raw)  # pylint: disable=protected-access
        assert result['root_cause'] == 'OOM'
        assert result['remediation'] == 'Increase limits'

    def test_parse_response_extracts_detailed_analysis(self):
        """_parse_response should surface detailed_analysis when the LLM includes it."""
        diagnoser = AIDiagnoser()
        raw = (
            '{"root_cause": "OOM kill",'
            ' "detailed_analysis": "The container exceeded its memory limit.",'
            ' "remediation": "Increase memory limits"}'
        )
        result = diagnoser._parse_response(raw)  # pylint: disable=protected-access
        assert result['detailed_analysis'] == 'The container exceeded its memory limit.'

    def test_parse_response_detailed_analysis_none_on_malformed(self):
        """_parse_response should return None for detailed_analysis when JSON is malformed."""
        diagnoser = AIDiagnoser()
        result = diagnoser._parse_response(  # pylint: disable=protected-access
            "This is not JSON"
        )
        assert result.get('detailed_analysis') is None


class TestAIDiagnoserGeminiFallback:
    """Tests for AIDiagnoser fallback to Gemini when OpenAI is unavailable."""

    def test_falls_back_to_gemini_when_openai_absent(self):
        """Should use Gemini when OPENAI_API_KEY is absent and GEMINI_API_KEY is set."""
        mock_response = '{"root_cause": "Config error", "remediation": "Fix config"}'
        env = {'OPENAI_API_KEY': '', 'GEMINI_API_KEY': 'test-gemini-key', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.gemini_analyzer.genai') as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.return_value = MagicMock(text=mock_response)
                diagnoser = AIDiagnoser()
                result = diagnoser.diagnose(SAMPLE_CONTEXT)
        assert result['root_cause'] == 'Config error'
        assert result['model_used'].startswith('gemini/')

    def test_suggest_returns_empty_string_without_provider(self):
        """suggest() should return empty string gracefully when no AI provider is available."""
        env = {'OPENAI_API_KEY': '', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            diagnoser = AIDiagnoser()
            result = diagnoser.suggest("Explain this Kubernetes issue")
        assert isinstance(result, str)


class TestOllamaAnalyzer:
    """Tests for OllamaAnalyzer error handling in analyze()."""

    def test_analyze_raises_runtime_error_on_http_status_error(self):
        """analyze() should raise RuntimeError when Ollama returns a non-2xx HTTP status."""
        import httpx  # pylint: disable=import-outside-toplevel
        from ai_engine.analyzers.ollama_analyzer import OllamaAnalyzer  # pylint: disable=import-outside-toplevel
        analyzer = OllamaAnalyzer()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        with patch('httpx.post', return_value=mock_response):
            with pytest.raises(RuntimeError, match="Ollama returned HTTP"):
                analyzer.analyze("test prompt")

    def test_analyze_raises_runtime_error_on_request_error(self):
        """analyze() should raise RuntimeError when the Ollama request fails (e.g. connection)."""
        import httpx  # pylint: disable=import-outside-toplevel
        from ai_engine.analyzers.ollama_analyzer import OllamaAnalyzer  # pylint: disable=import-outside-toplevel
        analyzer = OllamaAnalyzer()
        with patch('httpx.post', side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(RuntimeError, match="Ollama request failed"):
                analyzer.analyze("test prompt")


class TestAIDiagnoserAnalyzerCaching:
    """Tests for AIDiagnoser analyzer caching and routing logic."""

    def test_analyzer_cached_on_second_call(self):
        """_get_analyzer should return cached analyzer on subsequent calls."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.openai_analyzer.OpenAI'):
                diagnoser = AIDiagnoser()
                analyzer1 = diagnoser._get_analyzer()  # pylint: disable=protected-access
                analyzer2 = diagnoser._get_analyzer()  # pylint: disable=protected-access
                assert analyzer1 is analyzer2

    def test_ollama_is_available_true_uses_ollama(self):
        """Should use Ollama when OLLAMA_BASE_URL is set and Ollama is available."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': 'http://localhost:11434'}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.ollama_analyzer.OllamaAnalyzer.is_available', return_value=True):
                diagnoser = AIDiagnoser()
                analyzer = diagnoser._get_analyzer()  # pylint: disable=protected-access
                assert 'ollama' in analyzer.model_name.lower()

    def test_ollama_not_available_falls_back_to_openai(self):
        """Should fall back to OpenAI when Ollama is configured but not available."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': 'http://localhost:11434'}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.ollama_analyzer.OllamaAnalyzer.is_available', return_value=False):
                with patch('ai_engine.analyzers.openai_analyzer.OpenAI'):
                    diagnoser = AIDiagnoser()
                    analyzer = diagnoser._get_analyzer()  # pylint: disable=protected-access
                    assert 'openai' in analyzer.model_name.lower()


class TestAIDiagnoserSuggest:
    """Tests for the AIDiagnoser.suggest method."""

    def test_suggest_returns_result_with_provider(self):
        """suggest() should return AI response when provider is available."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.openai_analyzer.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = MagicMock(
                    choices=[MagicMock(message=MagicMock(content="This is the suggestion"))]
                )
                diagnoser = AIDiagnoser()
                result = diagnoser.suggest("Explain K8s probes")
        assert result == "This is the suggestion"

    def test_suggest_returns_empty_on_unexpected_error(self):
        """suggest() should return empty string on unexpected exception."""
        env = {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}
        with patch.dict(os.environ, env):
            with patch('ai_engine.analyzers.openai_analyzer.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = ValueError("Unexpected error")
                diagnoser = AIDiagnoser()
                result = diagnoser.suggest("Explain K8s probes")
        assert result == ""


class TestAIDiagnoserParseResponse:
    """Additional tests for _parse_response edge cases."""

    def test_parse_response_empty_string(self):
        """_parse_response should handle empty string gracefully."""
        diagnoser = AIDiagnoser()
        result = diagnoser._parse_response("")  # pylint: disable=protected-access
        assert result['root_cause'] == "No analysis available"
        assert result['detailed_analysis'] is None

    def test_parse_response_truncates_long_text(self):
        """_parse_response should truncate root_cause if raw text is very long."""
        diagnoser = AIDiagnoser()
        long_text = "A" * 1000
        result = diagnoser._parse_response(long_text)  # pylint: disable=protected-access
        assert len(result['root_cause']) <= 500

    def test_parse_response_json_without_fence(self):
        """_parse_response should handle JSON without markdown fence."""
        diagnoser = AIDiagnoser()
        raw = '{"root_cause": "Memory issue", "remediation": "Add more RAM", "detailed_analysis": "Details here"}'
        result = diagnoser._parse_response(raw)  # pylint: disable=protected-access
        assert result['root_cause'] == "Memory issue"
        assert result['detailed_analysis'] == "Details here"

    def test_parse_response_json_with_empty_detailed_analysis(self):
        """_parse_response should convert empty detailed_analysis to None."""
        diagnoser = AIDiagnoser()
        raw = '{"root_cause": "Issue", "remediation": "Fix it", "detailed_analysis": ""}'
        result = diagnoser._parse_response(raw)  # pylint: disable=protected-access
        assert result['detailed_analysis'] is None
