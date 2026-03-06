"""Utility helpers for data masking and Kubernetes resource classification."""
import re

SENSITIVE_PATTERNS = [
    (r'(?i)(password|passwd|token|secret|key|auth|api[_-]?key|credential)\s*[:=]\s*["\']?([\w\-\.\/\+\=]{4,})["\']?', r'\1: [MASKED]'),
    (r'(?i)(bearer\s+)([\w\-\.]{10,})', r'\1[MASKED]'),
    (r'(?i)(basic\s+)([\w\+\/\=]{10,})', r'\1[MASKED]'),
]


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
    test_str = 'The database password is "admin123" and api_key=xyz-123 bearer eyJhbGc...'
    print(f'Original: {test_str}')
    print(f'Masked:   {mask_sensitive_data(test_str)}')
