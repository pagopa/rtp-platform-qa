from requests import Request

from utils.type_utils import JsonType


def extract_id_from_location(location: str | None) -> str | None:
    """
    Extract the ID from a Location header URL.
    '.../activations/{id}' -> '{id}'.

    Returns None if location is None or empty.
    """
    if not location:
        return None
    return location.rstrip("/").split("/")[-1] or None


def serialize_json_payload(*, method: str, url: str, payload: JsonType) -> bytes:
    """Serialize a JSON payload as requests does for a prepared request."""
    prepared_request = Request(method=method, url=url, json=payload).prepare()
    if prepared_request.body is None:
        raise ValueError("Expected a serialized request body")
    return prepared_request.body if isinstance(prepared_request.body, bytes) else prepared_request.body.encode()
