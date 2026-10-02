"""Test EPC canonicalization for SRTP messages."""

import allure
import pytest

from utils.srtp_message_signing import build_canonical_representation, epc_header_filter

HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH")


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Reject an invalid HTTP target URI")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
@pytest.mark.parametrize(
    "url",
    (
        "/v1/resource",
        "mailto:api@example.com",
        "ftp://example.com/resource",
        "https://example.com/resource#fragment",
    ),
)
def test_canonical_representation_requires_a_complete_target_uri(url: str) -> None:
    """Reject target values that are not valid HTTP URIs."""
    with pytest.raises(ValueError, match="requires a complete target URI"):
        build_canonical_representation(method="GET", url=url, headers={}, body=b"")


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Sort headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_sorts_headers() -> None:
    """Sort and normalize headers in the canonical representation."""
    canonical = build_canonical_representation(
        method="GET",
        url="https://api.example.com",
        headers={"X-Request-ID": "b", "Content-Type": "a"},
        body=b"",
    )

    assert canonical == b"GET\nhttps://api.example.com\ncontent-type: a\nx-request-id: b", (
        "Expected headers to be lowercased and sorted in the canonical representation"
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve supported HTTP methods")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
@pytest.mark.parametrize("method", tuple(method.lower() for method in HTTP_METHODS))
def test_canonical_representation_emits_an_uppercase_method(method: str) -> None:
    """Normalize each supported HTTP method to uppercase."""
    canonical = build_canonical_representation(
        method=method,
        url="https://example.com",
        headers={"Content-Type": "application/json"},
        body=b"",
    )

    assert canonical.split(b"\n", maxsplit=1)[0] == method.upper().encode(), (
        f"Expected method {method!r} to be uppercased in the canonical representation"
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Filter headers outside the EPC API set")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_filters_headers_outside_the_epc_api_set() -> None:
    """Exclude transport headers outside the EPC API whitelist."""
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com",
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": "key",
            "Location": "https://api.example.com/resource/1",
            "X-Request-ID": "request",
            "Authorization": "secret",
        },
        body=b"",
    )

    assert canonical == (
        b"POST\nhttps://api.example.com\n"
        b"content-type: application/json\n"
        b"idempotency-key: key\n"
        b"location: https://api.example.com/resource/1\n"
        b"x-request-id: request"
    ), "Expected non-EPC headers to be excluded from the canonical representation"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Match EPC headers case-insensitively")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_matches_epc_headers_case_insensitively() -> None:
    """Match EPC headers regardless of their input casing."""
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com",
        headers={"CONTENT-TYPE": "application/json", "x-request-id": "request"},
        body=b"",
    )

    assert canonical == b"POST\nhttps://api.example.com\ncontent-type: application/json\nx-request-id: request", (
        "Expected EPC header matching to be case-insensitive"
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Match the EPC header filter case-insensitively")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_epc_header_filter_matches_swagger_headers_case_insensitively() -> None:
    """Validate the EPC header whitelist with case-insensitive names."""
    assert epc_header_filter("Content-Type"), "Content-Type should be included in the EPC header set"
    assert epc_header_filter("IDEMPOTENCY-KEY"), "Idempotency-Key should be included in the EPC header set"
    assert epc_header_filter("x-request-id"), "X-Request-ID should be included in the EPC header set"
    assert epc_header_filter("Location"), "Location should be included in the EPC header set"
    assert not epc_header_filter("Authorization"), "Authorization should be excluded from the EPC header set"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Apply a caller-provided header filter")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_applies_a_caller_provided_header_filter() -> None:
    """Apply a caller-provided predicate when selecting canonical headers."""
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com",
        headers={"Content-Type": "application/json", "X-Request-ID": "request"},
        body=b"",
        header_filter=lambda name: name == "x-request-id",
    )

    assert canonical == b"POST\nhttps://api.example.com\nx-request-id: request", (
        "Expected the caller-provided header filter to control included headers"
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Represent an empty message body")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_has_no_separator_for_an_empty_body() -> None:
    """Avoid adding a body separator when the payload is empty."""
    canonical = build_canonical_representation(
        method="GET",
        url="https://example.com",
        headers={},
        body=b"",
    )

    assert canonical == b"GET\nhttps://example.com", "Expected no separator after a message with an empty body"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve body bytes without headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_preserves_body_bytes_without_headers() -> None:
    """Preserve binary payload bytes when no headers are present."""
    canonical = build_canonical_representation(
        method="POST",
        url="https://example.com",
        headers={},
        body=bytes((0xFF, 0x00)),
    )

    assert canonical == b"POST\nhttps://example.com\n\xff\x00", "Expected body bytes to be preserved without headers"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve payload bytes after headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_preserves_payload_bytes_after_headers() -> None:
    """Preserve binary payload bytes after canonical headers."""
    payload = bytes((0x7B, 0xFF, 0x00, 0x0A, 0x7D))
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com/v1/resource",
        headers={"Content-Type": "application/octet-stream"},
        body=payload,
    )

    assert canonical == (
        b"POST\nhttps://api.example.com/v1/resource\ncontent-type: application/octet-stream\n\x7b\xff\x00\x0a\x7d"
    ), "Expected payload bytes to be preserved after the canonical headers"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Avoid a closing line feed")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_does_not_append_a_closing_line_feed() -> None:
    """Do not append a trailing line feed to the canonical message."""
    canonical = build_canonical_representation(
        method="POST",
        url="https://example.com",
        headers={"Content-Type": "application/json"},
        body=bytes((0x0A, 0x01)),
    )

    assert canonical[-1] == 0x01, "Expected the canonical representation to omit a closing line feed"
