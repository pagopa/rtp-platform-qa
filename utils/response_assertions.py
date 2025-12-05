import json

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
