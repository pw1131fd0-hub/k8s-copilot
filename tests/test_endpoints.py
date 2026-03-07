"""Endpoint integration tests for the Lobster K8s Copilot API."""
# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from kubernetes.client.exceptions import ApiException


@pytest.fixture
def client():
    """Return a TestClient wired to the FastAPI app with K8s config mocked out."""
    with patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.config.load_incluster_config'):
        from backend.main import app  # pylint: disable=import-outside-toplevel
        with TestClient(app) as c:
            yield c


def test_root_endpoint(client):
    """GET / should return HTTP 200 with the API running message."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json()['message'] == 'Lobster K8s Copilot API is running'


def test_cluster_status_endpoint(client):
    """GET /api/v1/cluster/status should return HTTP 200 with status, version, and message fields."""
    mock_version_info = MagicMock()
    mock_version_info.git_version = 'v1.28.0'
    with patch('kubernetes.client.CoreV1Api') as mock_v1, \
         patch('kubernetes.client.VersionApi') as mock_version:
        mock_v1.return_value.list_namespace.return_value = MagicMock(items=[])
        mock_version.return_value.get_code.return_value = mock_version_info
        response = client.get('/api/v1/cluster/status')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'connected'
    assert data['version'] == 'v1.28.0'
    assert data['message'] is None


def test_cluster_status_disconnected(client):
    """GET /api/v1/cluster/status should return disconnected with message when K8s unreachable."""
    with patch('kubernetes.client.CoreV1Api') as mock_v1:
        mock_v1.return_value.list_namespace.side_effect = Exception("Connection refused")
        response = client.get('/api/v1/cluster/status')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'disconnected'
    assert data['version'] is None
    # Security: Error message should be generic, not expose internal details
    assert data['message'] == 'Unable to connect to Kubernetes cluster'


def test_list_pods_endpoint(client):
    """GET /api/v1/cluster/pods should return a list containing the mocked pod."""
    mock_pod = MagicMock()
    mock_pod.metadata.name = 'test-pod'
    mock_pod.metadata.namespace = 'default'
    mock_pod.status.phase = 'Running'
    mock_pod.status.pod_ip = '10.0.0.1'
    mock_pod.status.conditions = []

    with patch('kubernetes.client.CoreV1Api') as mock_v1:
        mock_v1.return_value.list_pod_for_all_namespaces.return_value = MagicMock(items=[mock_pod])
        response = client.get('/api/v1/cluster/pods')

    assert response.status_code == 200
    data = response.json()
    assert 'pods' in data
    assert data['pods'][0]['name'] == 'test-pod'


def test_list_pods_endpoint_k8s_api_error_returns_empty(client):
    """list_pods should gracefully return an empty list on K8s API failures."""
    from backend.controllers.pod_controller import _svc  # pylint: disable=import-outside-toplevel
    mock_v1 = MagicMock()
    mock_v1.list_pod_for_all_namespaces.side_effect = ApiException(status=403, reason="Forbidden")
    _svc._v1 = mock_v1  # pylint: disable=protected-access
    try:
        response = client.get('/api/v1/cluster/pods')
    finally:
        _svc._v1 = None  # pylint: disable=protected-access

    assert response.status_code == 200
    data = response.json()
    assert data['pods'] == []
    assert data['total'] == 0


def test_list_pods_endpoint_namespace_filter(client):
    """GET /api/v1/cluster/pods?namespace=X should filter pods by namespace."""
    from backend.controllers.pod_controller import _svc  # pylint: disable=import-outside-toplevel
    mock_pod = MagicMock()
    mock_pod.metadata.name = 'ns-pod'
    mock_pod.metadata.namespace = 'kube-system'
    mock_pod.status.phase = 'Running'
    mock_pod.status.pod_ip = '10.0.0.2'
    mock_pod.status.conditions = []

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    _svc._v1 = mock_v1  # pylint: disable=protected-access
    try:
        response = client.get('/api/v1/cluster/pods?namespace=kube-system')
    finally:
        _svc._v1 = None  # pylint: disable=protected-access

    assert response.status_code == 200
    data = response.json()
    assert data['pods'][0]['namespace'] == 'kube-system'


def test_yaml_scan_endpoint_detects_issues(client):
    """POST /api/v1/yaml/scan should detect issues in a non-compliant manifest."""
    yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
spec:
  containers:
  - name: bad-container
    image: myapp:latest
"""
    response = client.post('/api/v1/yaml/scan', json={'yaml_content': yaml_content})
    assert response.status_code == 200
    data = response.json()
    assert 'issues' in data
    assert data['total_issues'] > 0


def test_yaml_scan_endpoint_invalid_yaml(client):
    """POST /api/v1/yaml/scan with unparseable YAML should return has_errors: true."""
    response = client.post('/api/v1/yaml/scan', json={'yaml_content': 'this: is: bad: yaml: :::'})
    assert response.status_code == 200
    data = response.json()
    assert data['has_errors'] is True


def test_yaml_scan_payload_too_large_returns_422(client):
    """yaml_content exceeding 512 KB should be rejected with HTTP 422."""
    oversized = "a: b\n" * (512 * 1024 // 5 + 1)
    response = client.post('/api/v1/yaml/scan', json={'yaml_content': oversized})
    assert response.status_code == 422


def test_yaml_diff_endpoint_detects_changes(client):
    """POST /api/v1/yaml/diff should return a non-empty diff when manifests differ."""
    response = client.post(
        '/api/v1/yaml/diff',
        json={'yaml_a': 'replicas: 1', 'yaml_b': 'replicas: 3'},
    )
    assert response.status_code == 200
    assert response.json() != {}


def test_yaml_diff_identical_yamls_returns_empty(client):
    """POST /api/v1/yaml/diff should return an empty dict when manifests are identical."""
    yaml = 'foo: bar\nbaz: 1'
    response = client.post('/api/v1/yaml/diff', json={'yaml_a': yaml, 'yaml_b': yaml})
    assert response.status_code == 200
    assert response.json() == {}


def test_yaml_diff_invalid_yaml_returns_error_key(client):
    """POST /api/v1/yaml/diff with invalid YAML should return a dict with an 'error' key."""
    response = client.post(
        '/api/v1/yaml/diff',
        json={'yaml_a': 'not: valid: yaml: :::', 'yaml_b': 'foo: bar'},
    )
    assert response.status_code == 200
    assert 'error' in response.json()


def test_yaml_diff_payload_too_large_returns_422(client):
    """POST /api/v1/yaml/diff with yaml_a exceeding 512 KB should be rejected with HTTP 422."""
    oversized = "a: b\n" * (512 * 1024 // 5 + 1)
    response = client.post('/api/v1/yaml/diff', json={'yaml_a': oversized, 'yaml_b': 'foo: bar'})
    assert response.status_code == 422


def test_diagnose_history_endpoint_returns_list(client):
    """GET /api/v1/diagnose/history should return a list (empty is valid)."""
    response = client.get('/api/v1/diagnose/history')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_diagnose_pod_history_endpoint_returns_list(client):
    """GET /api/v1/diagnose/history/{pod_name} should return a list for a known-good pod name."""
    response = client.get('/api/v1/diagnose/history/my-pod')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_diagnose_pod_history_invalid_name_returns_422(client):
    """GET /api/v1/diagnose/history/{pod_name} with an invalid pod name should return 422."""
    response = client.get('/api/v1/diagnose/history/Invalid_Pod_Name!')
    assert response.status_code == 422


def test_diagnose_pod_not_found_returns_404(client):
    """POST /api/v1/diagnose/{pod_name} should return 404 when the pod does not exist."""
    from backend.controllers.diagnose_controller import _svc  # pylint: disable=import-outside-toplevel

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(status=404, reason="Not Found")
    _svc._pod_service._v1 = mock_v1  # pylint: disable=protected-access
    try:
        response = client.post('/api/v1/diagnose/missing-pod', json={'namespace': 'default'})
    finally:
        _svc._pod_service._v1 = None  # pylint: disable=protected-access

    assert response.status_code == 404
    assert 'not found' in response.json()['detail'].lower()
