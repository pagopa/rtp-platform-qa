import re

def sanitize_bearer_token(text: str) -> str:
    """Remove bearer tokens from text to prevent exposure in logs/reports."""
    if not text or not isinstance(text, str):
        return text

    pattern = r'Bearer\s+[A-Za-z0-9_\-\.]{50,}'
    return re.sub(pattern, 'Bearer ***REDACTED***', text)
