from typing import Any, Dict, Optional
import pytest
from requests import Response


def is_empty_response(res: Response) -> bool:
    raw = res.text or ""
    return not raw.strip()


def ensure_json_response_and_type(res: Response) -> None:
    content_type = res.headers.get('Content-Type', '')
    assert 'json' in content_type.lower(), f'Expected JSON response, got Content-Type: {content_type}'


def validate_error_structure(body: Dict[str, Any]) -> None:
    if 'errors' in body:
        assert isinstance(body['errors'], list) and body['errors'], "Expected non-empty 'errors' list"
        first_err = body['errors'][0]
        assert 'code' in first_err and isinstance(first_err['code'], str), 'Missing/invalid error code'
        assert 'description' in first_err and isinstance(first_err['description'], str), 'Missing/invalid error description'
        return
    if 'message' in body:
        assert isinstance(body['message'], str) and body['message'], "Expected non-empty 'message'"
        if 'statusCode' in body:
            assert 400 <= int(body['statusCode']) < 500, f"Expected statusCode in 400-499 (4xx client error), but got {body['statusCode']}"
        return
    pytest.fail("Expected 'errors' or 'message' in error response body")


def validate_activations_and_meta(body: Dict[str, Any]) -> None:
    if 'activations' in body:
        assert isinstance(body['activations'], list) and len(body['activations']) == 0, "Unexpected 'activations' content in error response"
    meta: Optional[Dict[str, Any]] = body.get('metadata') or body.get('page')
    if isinstance(meta, dict):
        assert not meta.get('nextActivationId'), "Unexpected 'nextActivationId' in error metadata"