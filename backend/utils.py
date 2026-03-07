"""Utility helpers for data masking and Kubernetes resource classification."""
import re

# Kubernetes DNS-subdomain name regex (covers pod names, namespaces, etc.)
K8S_NAME_RE = re.compile(r'^[a-z0-9]([a-z0-9\-]{0,251}[a-z0-9])?$')

SENSITIVE_PATTERNS = [
    (
        r'(?i)(password|passwd|token|secret|key|auth|api[_-]?key|credential)'
        r'\s*[:=]\s*["\']?([\w\-\.\/\+\=]{4,})["\']?',
        r'\1: [MASKED]',
    ),
    (r'(?i)(bearer\s+)([\w\-\.]{10,})', r'\1[MASKED]'),
    (r'(?i)(basic\s+)([\w\+\/\=]{10,})', r'\1[MASKED]'),
    # JSON/YAML inline secrets: "password":"value" or password: value
    (
        r'(?i)(["\']?(password|passwd|secret|token|api[_-]?key)["\']?\s*:\s*["\']?)'
        r'([\w\-\.\/\+\=]{4,})["\']?',
        r'\1[MASKED]',
    ),
    # Database URLs with embedded credentials: postgres://user:pass@host
    (r'(?i)(\w+://[\w\-\.]+:)([\w\-\.\/\+\=\@]{4,})(@)', r'\1[MASKED]\3'),
    # AWS access key IDs and secret access keys
    (r'(?i)(AKIA[A-Z0-9]{16})', r'[MASKED-AWS-KEY]'),
    (r'(?i)(aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*)([A-Za-z0-9\/\+\=]{20,})', r'\1[MASKED]'),
]


class PodNotFoundError(Exception):
    """Raised when a Kubernetes pod cannot be found (HTTP 404 from the K8s API)."""

    def __init__(self, pod_name: str, namespace: str) -> None:
        self.pod_name = pod_name
        self.namespace = namespace
        super().__init__(f"Pod '{pod_name}' not found in namespace '{namespace}'")


def mask_sensitive_data(text: str) -> str:
    """Masks common sensitive patterns like passwords, tokens, and API keys."""
    masked_text = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked_text = re.sub(pattern, replacement, masked_text)
    return masked_text


def is_secret_resource(yaml_dict: dict) -> bool:
    """Returns True if the K8s resource is a Secret kind (should not be sent to LLM)."""
    return yaml_dict.get("kind", "").lower() == "secret"


if __name__ == '__main__':
    _example = 'The database password is "admin123" and api_key=xyz-123 bearer eyJhbGc...'  # pylint: disable=invalid-name
    print(f'Original: {_example}')
    print(f'Masked:   {mask_sensitive_data(_example)}')
