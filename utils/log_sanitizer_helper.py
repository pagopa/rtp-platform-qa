import re


def sanitize_bearer_token(text: str) -> str:
    """Remove bearer tokens from text to prevent exposure in logs/reports."""
    if not text or not isinstance(text, str):
        return text

    text = re.sub(r"Bearer\s+([\w-]*\.[\w-]*\.[\w-]*)", "Bearer ***REDACTED***", text)

    text = re.sub(r"\beyJ([\w-]*\.[\w-]*\.[\w-]*)", "***REDACTED_JWT***", text)

    return text
