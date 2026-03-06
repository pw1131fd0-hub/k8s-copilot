import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def patch_k8s():
    with patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.config.load_incluster_config'):
        yield
