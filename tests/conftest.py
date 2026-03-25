"""Shared pytest fixtures for Lobster K8s Copilot tests."""
import os
import sys
from unittest.mock import patch

import pytest

# Add the project root to sys.path so test modules can import project packages.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def patch_k8s():
    """Auto-use fixture that prevents real Kubernetes config loading during tests."""
    with patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.config.load_incluster_config'):
        yield
