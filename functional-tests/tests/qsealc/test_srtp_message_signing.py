import allure
import pytest

from utils.srtp_message_signing import build_canonical_representation, epc_header_filter

HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH")


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Reject an incomplete target URI")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
@pytest.mark.parametrize("url", ("/v1/resource", "mailto:api@example.com"))
def test_canonical_representation_requires_a_complete_target_uri(url: str) -> None:
    with pytest.raises(ValueError, match="requires a complete target URI"):
        build_canonical_representation(method="GET", url=url, headers={}, body=b"")


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Uppercase the method and sort headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_uppercases_method_and_sorts_headers() -> None:
    canonical = build_canonical_representation(
        method="get",
        url="https://api.example.com",
        headers={"X-Request-ID": "b", "Content-Type": "a"},
        body=b"",
    )

    assert canonical == b"GET\nhttps://api.example.com\ncontent-type: a\nx-request-id: b"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve supported HTTP methods")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
@pytest.mark.parametrize("method", HTTP_METHODS)
def test_canonical_representation_emits_an_uppercase_method(method: str) -> None:
    canonical = build_canonical_representation(
        method=method,
        url="https://example.com",
        headers={"Content-Type": "application/json"},
        body=b"",
    )

    assert canonical.split(b"\n", maxsplit=1)[0] == method.encode()


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Filter headers outside the EPC API set")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_filters_headers_outside_the_epc_api_set() -> None:
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
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Match EPC headers case-insensitively")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_matches_epc_headers_case_insensitively() -> None:
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com",
        headers={"CONTENT-TYPE": "application/json", "x-request-id": "request"},
        body=b"",
    )

    assert canonical == b"POST\nhttps://api.example.com\ncontent-type: application/json\nx-request-id: request"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Match the EPC header filter case-insensitively")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_epc_header_filter_matches_swagger_headers_case_insensitively() -> None:
    assert epc_header_filter("Content-Type")
    assert epc_header_filter("IDEMPOTENCY-KEY")
    assert epc_header_filter("x-request-id")
    assert epc_header_filter("Location")
    assert not epc_header_filter("Authorization")


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Apply a caller-provided header filter")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_applies_a_caller_provided_header_filter() -> None:
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com",
        headers={"Content-Type": "application/json", "X-Request-ID": "request"},
        body=b"",
        header_filter=lambda name: name == "x-request-id",
    )

    assert canonical == b"POST\nhttps://api.example.com\nx-request-id: request"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Represent an empty message body")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_has_no_separator_for_an_empty_body() -> None:
    canonical = build_canonical_representation(
        method="GET",
        url="https://example.com",
        headers={},
        body=b"",
    )

    assert canonical == b"GET\nhttps://example.com"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve body bytes without headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_preserves_body_bytes_without_headers() -> None:
    canonical = build_canonical_representation(
        method="POST",
        url="https://example.com",
        headers={},
        body=bytes((0xFF, 0x00)),
    )

    assert canonical == b"POST\nhttps://example.com\n\xff\x00"


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Preserve payload bytes after headers")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_preserves_payload_bytes_after_headers() -> None:
    payload = bytes((0x7B, 0xFF, 0x00, 0x0A, 0x7D))
    canonical = build_canonical_representation(
        method="POST",
        url="https://api.example.com/v1/resource",
        headers={"Content-Type": "application/octet-stream"},
        body=payload,
    )

    assert canonical == (
        b"POST\nhttps://api.example.com/v1/resource\ncontent-type: application/octet-stream\n\x7b\xff\x00\x0a\x7d"
    )


@allure.epic("QSealC message signing")
@allure.feature("Canonical representation")
@allure.story("Avoid a closing line feed")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_canonical_representation_does_not_append_a_closing_line_feed() -> None:
    canonical = build_canonical_representation(
        method="POST",
        url="https://example.com",
        headers={"Content-Type": "application/json"},
        body=bytes((0x0A, 0x01)),
    )

    assert canonical[-1] == 0x01
