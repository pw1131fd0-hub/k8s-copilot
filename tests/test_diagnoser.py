import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch, MagicMock
from ai_engine.diagnoser import AIDiagnoser


SAMPLE_CONTEXT = {
    "pod_name": "test-pod",
    "namespace": "default",
    "error_type": "CrashLoopBackOff",
    "describe": "Phase: Failed\nEvents:\nBackOff: Back-off restarting failed container",
    "logs": "Error: cannot connect to database at db:5432",
}


class TestAIDiagnoserNoProvider:
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


class TestAIDiagnoserWithMock:
    def test_uses_openai_when_configured(self):
        mock_response = '{"root_cause": "DB connection refused", "remediation": "kubectl exec..."}'
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test', 'GEMINI_API_KEY': '', 'OLLAMA_BASE_URL': ''}):
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

    def test_parse_response_handles_malformed_json(self):
        diagnoser = AIDiagnoser()
        result = diagnoser._parse_response("Not valid JSON but contains useful info")
        assert 'root_cause' in result
        assert 'remediation' in result

    def test_parse_response_extracts_json_from_markdown(self):
        diagnoser = AIDiagnoser()
        raw = '```json\n{"root_cause": "OOM", "remediation": "Increase limits"}\n```'
        result = diagnoser._parse_response(raw)
        assert result['root_cause'] == 'OOM'
        assert result['remediation'] == 'Increase limits'
