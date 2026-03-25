"""Tests for PodService - Kubernetes API interactions."""
import pytest
from unittest.mock import MagicMock, patch
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import MaxRetryError, ReadTimeoutError

from backend.services.pod_service import PodService, _format_container_statuses
from backend.utils import PodNotFoundError


class TestFormatContainerStatuses:
    """Tests for _format_container_statuses helper function."""

    def test_empty_list_returns_none_text(self):
        """Should return '(none)' for empty list."""
        result = _format_container_statuses([])
        assert result == "  (none)"

    def test_none_input_returns_none_text(self):
        """Should return '(none)' for None input."""
        result = _format_container_statuses(None)
        assert result == "  (none)"

    def test_waiting_state_format(self):
        """Should format waiting container state."""
        mock_status = MagicMock()
        mock_status.name = "app"
        mock_status.ready = False
        mock_status.restart_count = 5
        mock_status.state.waiting = MagicMock()
        mock_status.state.waiting.reason = "CrashLoopBackOff"
        mock_status.state.running = None
        mock_status.state.terminated = None

        result = _format_container_statuses([mock_status])
        assert "app:" in result
        assert "CrashLoopBackOff" in result
        assert "restartCount=5" in result

    def test_running_state_format(self):
        """Should format running container state."""
        mock_status = MagicMock()
        mock_status.name = "web"
        mock_status.ready = True
        mock_status.restart_count = 0
        mock_status.state.waiting = None
        mock_status.state.running = MagicMock()
        mock_status.state.terminated = None

        result = _format_container_statuses([mock_status])
        assert "web:" in result
        assert "Running" in result
        assert "ready=True" in result

    def test_terminated_state_format(self):
        """Should format terminated container state."""
        mock_status = MagicMock()
        mock_status.name = "sidecar"
        mock_status.ready = False
        mock_status.restart_count = 1
        mock_status.state.waiting = None
        mock_status.state.running = None
        mock_status.state.terminated = MagicMock()

        result = _format_container_statuses([mock_status])
        assert "sidecar:" in result
        assert "Terminated" in result

    def test_waiting_without_reason(self):
        """Should handle waiting state without explicit reason."""
        mock_status = MagicMock()
        mock_status.name = "init"
        mock_status.ready = False
        mock_status.restart_count = 0
        mock_status.state.waiting = MagicMock()
        mock_status.state.waiting.reason = None
        mock_status.state.running = None
        mock_status.state.terminated = None

        result = _format_container_statuses([mock_status])
        assert "Waiting" in result


class TestPodServiceListPods:
    """Tests for PodService.list_pods method."""

    @pytest.fixture
    def pod_service(self):
        """Return a PodService with mocked K8s client."""
        with patch('kubernetes.config.load_kube_config'), \
             patch('kubernetes.config.load_incluster_config'):
            return PodService()

    def test_list_all_pods(self, pod_service):
        """Should list pods from all namespaces."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.status.pod_ip = "10.0.0.1"
        mock_pod.status.conditions = None

        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.return_value = MagicMock(items=[mock_pod])
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert result.total == 1
        assert result.pods[0].name == "test-pod"
        mock_v1.list_pod_for_all_namespaces.assert_called_once()

    def test_list_pods_with_namespace_filter(self, pod_service):
        """Should filter pods by namespace."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "ns-pod"
        mock_pod.metadata.namespace = "kube-system"
        mock_pod.status.phase = "Running"
        mock_pod.status.pod_ip = "10.0.0.2"
        mock_pod.status.conditions = []

        mock_v1 = MagicMock()
        mock_v1.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        pod_service._v1 = mock_v1

        result = pod_service.list_pods(namespace="kube-system")

        assert result.total == 1
        assert result.pods[0].namespace == "kube-system"
        mock_v1.list_namespaced_pod.assert_called_once()

    def test_list_pods_with_conditions(self, pod_service):
        """Should include pod conditions in response."""
        mock_condition = MagicMock()
        mock_condition.type = "Ready"
        mock_condition.status = "True"

        mock_pod = MagicMock()
        mock_pod.metadata.name = "pod-with-conditions"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.status.pod_ip = "10.0.0.3"
        mock_pod.status.conditions = [mock_condition]

        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.return_value = MagicMock(items=[mock_pod])
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert len(result.pods[0].conditions) == 1
        assert result.pods[0].conditions[0]["type"] == "Ready"

    def test_list_pods_timeout_returns_empty(self, pod_service):
        """Should return empty list on timeout."""
        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.side_effect = ReadTimeoutError(
            pool=None, url="", message="Read timed out"
        )
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert result.total == 0
        assert result.pods == []

    def test_list_pods_max_retry_error_returns_empty(self, pod_service):
        """Should return empty list on max retry error."""
        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.side_effect = MaxRetryError(
            pool=None, url=""
        )
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert result.total == 0
        assert result.pods == []

    def test_list_pods_api_exception_returns_empty(self, pod_service):
        """Should return empty list on K8s API exception."""
        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.side_effect = ApiException(
            status=403, reason="Forbidden"
        )
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert result.total == 0
        assert result.pods == []

    def test_list_pods_unexpected_error_returns_empty(self, pod_service):
        """Should return empty list on unexpected exception."""
        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.side_effect = RuntimeError("Unexpected")
        pod_service._v1 = mock_v1

        result = pod_service.list_pods()

        assert result.total == 0
        assert result.pods == []


class TestPodServiceGetPodContext:
    """Tests for PodService.get_pod_context method."""

    @pytest.fixture
    def pod_service(self):
        """Return a PodService with mocked K8s client."""
        with patch('kubernetes.config.load_kube_config'), \
             patch('kubernetes.config.load_incluster_config'):
            return PodService()

    def _create_mock_pod(self, phase="Running", waiting_reason=None, terminated_reason=None):
        """Helper to create a mock pod object."""
        mock_pod = MagicMock()
        mock_pod.status.phase = phase
        
        mock_container_status = MagicMock()
        mock_container_status.name = "app"
        mock_container_status.ready = True
        mock_container_status.restart_count = 0
        mock_container_status.state.waiting = None
        mock_container_status.state.running = MagicMock()
        mock_container_status.state.terminated = None

        if waiting_reason:
            mock_container_status.ready = False
            mock_container_status.state.waiting = MagicMock()
            mock_container_status.state.waiting.reason = waiting_reason
            mock_container_status.state.running = None

        if terminated_reason:
            mock_container_status.ready = False
            mock_container_status.state.terminated = MagicMock()
            mock_container_status.state.terminated.reason = terminated_reason
            mock_container_status.state.running = None
            mock_container_status.state.waiting = None

        mock_pod.status.container_statuses = [mock_container_status]
        return mock_pod

    def test_get_pod_context_running_pod(self, pod_service):
        """Should collect context for a running pod."""
        mock_pod = self._create_mock_pod(phase="Running")
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.return_value = "Application started successfully"
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("test-pod", "default")

        assert result["pod_name"] == "test-pod"
        assert result["namespace"] == "default"
        assert result["error_type"] == "Unknown"
        assert "Running" in result["describe"]

    def test_get_pod_context_crashloopbackoff(self, pod_service):
        """Should detect CrashLoopBackOff error type."""
        mock_pod = self._create_mock_pod(phase="Running", waiting_reason="CrashLoopBackOff")

        mock_event = MagicMock()
        mock_event.reason = "BackOff"
        mock_event.message = "Back-off restarting failed container"
        mock_events = MagicMock()
        mock_events.items = [mock_event]

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.return_value = "Error: connection refused"
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("crashing-pod", "default")

        assert result["error_type"] == "CrashLoopBackOff"
        assert "BackOff" in result["describe"]

    def test_get_pod_context_terminated_state(self, pod_service):
        """Should detect terminated container reason."""
        mock_pod = self._create_mock_pod(phase="Failed", terminated_reason="OOMKilled")
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.return_value = "Killed"
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("oom-pod", "default")

        assert result["error_type"] == "OOMKilled"

    def test_get_pod_context_pending_pod(self, pod_service):
        """Should detect Pending state as error type."""
        mock_pod = MagicMock()
        mock_pod.status.phase = "Pending"
        mock_pod.status.container_statuses = None
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.return_value = ""
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("pending-pod", "default")

        assert result["error_type"] == "Pending"

    def test_get_pod_context_not_found_raises(self, pod_service):
        """Should raise PodNotFoundError when pod doesn't exist."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.side_effect = ApiException(status=404, reason="Not Found")
        pod_service._v1 = mock_v1

        with pytest.raises(PodNotFoundError) as exc_info:
            pod_service.get_pod_context("missing-pod", "default")

        assert "missing-pod" in str(exc_info.value)

    def test_get_pod_context_describe_timeout(self, pod_service):
        """Should handle timeout when describing pod."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.side_effect = ReadTimeoutError(
            pool=None, url="", message="Read timed out"
        )
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("slow-pod", "default")

        assert "timed out" in result["describe"].lower()

    def test_get_pod_context_describe_max_retry(self, pod_service):
        """Should handle max retry error when describing pod."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.side_effect = MaxRetryError(pool=None, url="")
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("retry-pod", "default")

        assert "timed out" in result["describe"].lower()

    def test_get_pod_context_describe_api_error(self, pod_service):
        """Should handle non-404 API errors when describing pod."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.side_effect = ApiException(status=403, reason="Forbidden")
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("forbidden-pod", "default")

        assert "403" in result["describe"]

    def test_get_pod_context_describe_unexpected_error(self, pod_service):
        """Should handle unexpected errors when describing pod."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.side_effect = RuntimeError("Unexpected error")
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("error-pod", "default")

        assert "Could not describe pod" in result["describe"]

    def test_get_pod_context_log_timeout(self, pod_service):
        """Should handle timeout when fetching logs."""
        mock_pod = self._create_mock_pod()
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.side_effect = ReadTimeoutError(
            pool=None, url="", message="Log timeout"
        )
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("log-timeout-pod", "default")

        assert "timed out" in result["logs"].lower()

    def test_get_pod_context_log_api_error(self, pod_service):
        """Should handle API error when fetching logs."""
        mock_pod = self._create_mock_pod()
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.side_effect = ApiException(
            status=400, reason="Container not found"
        )
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("no-logs-pod", "default")

        assert "400" in result["logs"]

    def test_get_pod_context_log_unexpected_error(self, pod_service):
        """Should handle unexpected error when fetching logs."""
        mock_pod = self._create_mock_pod()
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.side_effect = RuntimeError("Log fetch failed")
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("log-error-pod", "default")

        assert "Could not retrieve logs" in result["logs"]

    def test_get_pod_context_terminated_completed_ignored(self, pod_service):
        """Should not treat 'Completed' termination as error."""
        mock_pod = MagicMock()
        mock_pod.status.phase = "Succeeded"
        
        mock_cs = MagicMock()
        mock_cs.name = "job"
        mock_cs.ready = False
        mock_cs.restart_count = 0
        mock_cs.state.waiting = None
        mock_cs.state.running = None
        mock_cs.state.terminated = MagicMock()
        mock_cs.state.terminated.reason = "Completed"
        
        mock_pod.status.container_statuses = [mock_cs]
        mock_events = MagicMock()
        mock_events.items = []

        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod.return_value = mock_pod
        mock_v1.list_namespaced_event.return_value = mock_events
        mock_v1.read_namespaced_pod_log.return_value = "Job completed"
        pod_service._v1 = mock_v1

        result = pod_service.get_pod_context("job-pod", "default")

        # Should not set error_type to "Completed"
        assert result["error_type"] == "Unknown"
