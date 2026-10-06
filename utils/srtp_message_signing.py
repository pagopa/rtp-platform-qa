"""Canonicalize SRTP HTTP messages for QSealC signing."""

from collections.abc import Callable, Mapping
from urllib.parse import urlparse

from requests import PreparedRequest, Request

from utils.type_utils import JsonType

EPC_API_HEADERS = frozenset({"content-type", "idempotency-key", "location", "x-request-id"})
HTTP_SCHEMES = frozenset({"http", "https"})
HeaderFilter = Callable[[str], bool]


def epc_header_filter(header_name: str) -> bool:
    """Return whether a header is defined by the EPC API."""
    return header_name.lower() in EPC_API_HEADERS


def prepared_request_body(prepared_request: PreparedRequest) -> bytes:
    """Return a prepared request body as bytes."""
    if prepared_request.body is None:
        return b""
    if isinstance(prepared_request.body, bytes):
        return prepared_request.body
    if isinstance(prepared_request.body, str):
        return prepared_request.body.encode()
    raise TypeError("Prepared request body must be bytes or text")


def serialize_json_request_body(*, method: str, url: str, payload: JsonType) -> bytes:
    """Serialize a JSON request body exactly as Requests does."""
    return prepared_request_body(Request(method=method, url=url, json=payload).prepare())


def build_canonical_representation(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    header_filter: HeaderFilter = epc_header_filter,
) -> bytes:
    """Build the canonical byte representation of an SRTP HTTP message."""
    try:
        parsed_url = urlparse(url)
        port = parsed_url.port
        complete_target_uri = (
            parsed_url.scheme.lower() in HTTP_SCHEMES
            and bool(parsed_url.hostname)
            and "#" not in url
            and (port is None or port >= 0)
        )
    except ValueError:
        complete_target_uri = False

    if not complete_target_uri:
        raise ValueError("build_canonical_representation requires a complete target URI")

    canonical_headers = sorted((name.lower(), value) for name, value in headers.items() if header_filter(name.lower()))
    canonical_header_lines = [f"{name}: {value}".encode() for name, value in canonical_headers]
    canonical_message = [
        method.upper().encode(),
        b"\n",
        url.encode(),
        b"\n",
        b"\n".join(canonical_header_lines),
        b"\n",
        body,
    ]

    return b"".join(canonical_message)
