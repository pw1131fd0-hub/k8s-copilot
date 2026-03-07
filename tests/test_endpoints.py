import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from kubernetes.client.exceptions import ApiException


@pytest.fixture
def client():
    # Patch K8s config loading to avoid requiring a real cluster
    with patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.config.load_incluster_config'):
        from backend.main import app
        return TestClient(app)


def test_root_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json()['message'] == 'Lobster K8s Copilot API is running'


def test_cluster_status_endpoint(client):
    with patch('kubernetes.client.CoreV1Api') as mock_v1:
        mock_v1.return_value.list_namespace.return_value = MagicMock(items=[])
        response = client.get('/api/v1/cluster/status')
    assert response.status_code == 200
    assert 'status' in response.json()


def test_list_pods_endpoint(client):
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
    from backend.controllers.pod_controller import _svc
    mock_v1 = MagicMock()
    mock_v1.list_pod_for_all_namespaces.side_effect = ApiException(status=403, reason="Forbidden")
    _svc._v1 = mock_v1
    try:
        response = client.get('/api/v1/cluster/pods')
    finally:
        _svc._v1 = None  # reset cached client

    assert response.status_code == 200
    data = response.json()
    assert data['pods'] == []
    assert data['total'] == 0


def test_list_pods_endpoint_namespace_filter(client):
    from backend.controllers.pod_controller import _svc
    mock_pod = MagicMock()
    mock_pod.metadata.name = 'ns-pod'
    mock_pod.metadata.namespace = 'kube-system'
    mock_pod.status.phase = 'Running'
    mock_pod.status.pod_ip = '10.0.0.2'
    mock_pod.status.conditions = []

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    _svc._v1 = mock_v1
    try:
        response = client.get('/api/v1/cluster/pods?namespace=kube-system')
    finally:
        _svc._v1 = None  # reset cached client

    assert response.status_code == 200
    data = response.json()
    assert data['pods'][0]['namespace'] == 'kube-system'


def test_yaml_scan_endpoint_detects_issues(client):
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
    response = client.post('/api/v1/yaml/scan', json={'yaml_content': 'this: is: bad: yaml: :::'})
    assert response.status_code == 200
    data = response.json()
    assert data['has_errors'] is True


def test_yaml_scan_payload_too_large_returns_422(client):
    """yaml_content exceeding 512 KB should be rejected with HTTP 422."""
    oversized = "a: b\n" * (512 * 1024 // 5 + 1)
    response = client.post('/api/v1/yaml/scan', json={'yaml_content': oversized})
    assert response.status_code == 422
