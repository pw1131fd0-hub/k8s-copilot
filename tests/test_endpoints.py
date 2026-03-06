import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


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
