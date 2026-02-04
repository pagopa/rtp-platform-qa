from typing import Any
from typing import Optional

from requests import Response


def is_empty_response(res: Response) -> bool:
    """
    Return True if the HTTP response body is:
    - empty or whitespace-only, or
    - a JSON object with:
        {
            "activations": [],
            "metadata": {
                "nextActivationId": null,
                "size": <any>
            }
        }
    """
    raw = res.text or ''
    if not raw.strip():
        return True

    try:
        body = res.json()
    except ValueError:
        return False

    if not isinstance(body, dict):
        return False

    activations = body.get('activations')
    metadata = body.get('metadata')

    return (
        activations == [] and
        isinstance(metadata, dict) and
        'nextActivationId' in metadata and
        metadata['nextActivationId'] is None and
        'size' in metadata
    )


def get_response_body_safe(response: Response) -> Optional[Any]:
    """
    Safely parse JSON response body.
    Returns the parsed JSON or None if the response is not valid JSON.
    """
    try:
        return response.json()
    except ValueError:
        return None


def assert_response_code(
    response: Response,
    expected_code: int,
    operation: str,
    status: str
) -> None:
    """
    Assert that the response has the expected status code.
    Provides a detailed error message if the assertion fails.
    """
    assert response.status_code == expected_code, (
        f"Expected {expected_code} for {operation} with status {status}, "
        f"got {response.status_code}. Response: {response.text}"
    )


def assert_body_presence(
    body: Optional[Any],
    should_have_body: bool,
    operation: str,
    status: str
) -> None:
    """
    Assert that the response body is present or absent as expected.
    """
    if should_have_body:
        assert body, (
            f"Expected non-empty body for {operation} with status {status}, "
            f"got empty response"
        )
    else:
        assert not body, (
            f"Expected empty body for {operation} with status {status}, "
            f"got: {body}"
        )
