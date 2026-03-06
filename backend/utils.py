import re

def mask_sensitive_data(text: str) -> str:
    """Masks common sensitive patterns like passwords and tokens."""
    patterns = [
        (r'(?i)(password|token|secret|key|auth|api_key)\s*[:=]\s*("?[\w\-\.\/]+)[" \t\n]?', r'\1: [MASKED]')
    ]
    masked_text = text
    for pattern, replacement in patterns:
        masked_text = re.sub(pattern, replacement, masked_text)
    return masked_text

if __name__ == '__main__':
    test_str = 'The database password is "admin123" and api_key=xyz-123.'
    print(f'Original: {test_str}')
    print(f'Masked:   {mask_sensitive_data(test_str)}')
