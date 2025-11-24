"""
Utility functions for sanitizing sensitive data in test reports.
Removes Bearer tokens and other sensitive information from test outputs.
"""
import re


def sanitize_bearer_token(text):
    """
    Remove bearer tokens from text to prevent exposure in reports.
    
    Args:
        text: Text potentially containing bearer tokens
        
    Returns:
        Text with bearer tokens replaced by '***REDACTED***'
    """
    if not text or not isinstance(text, str):
        return text

    pattern = r'Bearer\s+[A-Za-z0-9_\-\.]{50,}'
    return re.sub(pattern, 'Bearer ***REDACTED***', text)


def sanitize_dict(obj):
    """
    Recursively sanitize dictionary values, removing sensitive data.
    
    Args:
        obj: Dictionary, list, or other object to sanitize
        
    Returns:
        Sanitized copy of the object
    """
    if isinstance(obj, dict):
        return {k: sanitize_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_dict(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_bearer_token(obj)
    return obj