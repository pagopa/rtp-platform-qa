import re

def sanitize_bearer_token(text: str) -> str:
    """Remove bearer tokens from text to prevent exposure in logs/reports."""
    if not text or not isinstance(text, str):
        return text

    text = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]{20,}', 'Bearer ***REDACTED***', text)

    text = re.sub(r'\beyJ[A-Za-z0-9_\-\.]{20,}', '***REDACTED_JWT***', text)

    return text
