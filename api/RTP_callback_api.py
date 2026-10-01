from collections.abc import Mapping

import requests
from requests import Response

from api.utils.api_version import CALLBACK_VERSION, CALLBACK_VERSION_V2, RFC_CALLBACK_VERSION, RFC_CALLBACK_VERSION_V2
from api.utils.endpoints import (
    CALLBACK_URL,
    CALLBACK_URL_V2,
    RFC_CALLBACK_URL,
    RFC_CALLBACK_URL_V2,
    STATUS_UPDATE_CALLBACK_URL,
)
from api.utils.http_utils import HTTP_TIMEOUT
from utils.type_utils import JsonType
from utils.cryptography_utils import QsealcKeyMaterial
from utils.srtp_signature import sign_srtp_message


def srtp_callback(
    cert_path: str,
    key_path: str,
    rtp_payload,
    include_version_header: bool = False,
    qsealc_key_material: QsealcKeyMaterial | None = None,
):
    headers = {"Version": CALLBACK_VERSION} if include_version_header else {}
    return _send_callback(
        cert_path=cert_path,
        key_path=key_path,
        url=CALLBACK_URL,
        headers=headers,
        rtp_payload=rtp_payload,
        qsealc_key_material=qsealc_key_material,
    )


def srtp_callback_v2(
    cert_path: str,
    key_path: str,
    rtp_payload,
    include_version_header: bool = False,
    qsealc_key_material: QsealcKeyMaterial | None = None,
):
    """
    Send a callback to the v2 RTP callback endpoint.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the key file
        rtp_payload: The callback payload
        include_version_header: When True, adds the Version header to the request

    Returns:
        Response object from the callback request
    """
    headers = {"Version": CALLBACK_VERSION_V2} if include_version_header else {}
    return _send_callback(
        cert_path=cert_path,
        key_path=key_path,
        url=CALLBACK_URL_V2,
        headers=headers,
        rtp_payload=rtp_payload,
        qsealc_key_material=qsealc_key_material,
    )


def srtp_status_update_callback(
    cert_path: str,
    key_path: str,
    rtp_payload: JsonType,
    extra_headers: Mapping[str, str] | None = None,
) -> Response:
    """Send a status-update callback to the v2 RTP callback endpoint."""
    headers = dict(extra_headers or {})
    return requests.post(
        cert=(cert_path, key_path),
        url=STATUS_UPDATE_CALLBACK_URL,
        headers=headers,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT,
    )


def srtp_rfc_callback(
    cert_path: str,
    key_path: str,
    rtp_payload,
    include_version_header: bool = False,
    qsealc_key_material: QsealcKeyMaterial | None = None,
):
    """
    Send RFC (Request for Cancellation) callback.

    This is used for DS12P and DS12N callbacks which use a different endpoint
    than regular RTP callbacks.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the key file
        rtp_payload: The RFC callback payload (DS12P or DS12N)
        include_version_header: When True, adds the Version header to the request

    Returns:
        Response object from the callback request
    """
    headers = {"Version": RFC_CALLBACK_VERSION} if include_version_header else {}
    return _send_callback(
        cert_path=cert_path,
        key_path=key_path,
        url=RFC_CALLBACK_URL,
        headers=headers,
        rtp_payload=rtp_payload,
        qsealc_key_material=qsealc_key_material,
    )


def srtp_rfc_callback_v2(
    cert_path: str,
    key_path: str,
    rtp_payload,
    include_version_header: bool = False,
    qsealc_key_material: QsealcKeyMaterial | None = None,
):
    """
    Send RFC (Request for Cancellation) callback to the v2 endpoint.

    This is used for v2 DS12P and DS12N callbacks which use a different endpoint
    than regular RTP callbacks.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the key file
        rtp_payload: The RFC callback payload (DS12P or DS12N)
        include_version_header: When True, adds the Version header to the request

    Returns:
        Response object from the callback request
    """
    headers = {"Version": RFC_CALLBACK_VERSION_V2} if include_version_header else {}
    return _send_callback(
        cert_path=cert_path,
        key_path=key_path,
        url=RFC_CALLBACK_URL_V2,
        headers=headers,
        rtp_payload=rtp_payload,
        qsealc_key_material=qsealc_key_material,
    )


def _send_callback(
    *,
    cert_path: str,
    key_path: str,
    url: str,
    headers: Mapping[str, str],
    rtp_payload,
    qsealc_key_material: QsealcKeyMaterial | None,
):
    if qsealc_key_material is None:
        return requests.post(
            cert=(cert_path, key_path),
            url=url,
            headers=headers,
            json=rtp_payload,
            timeout=HTTP_TIMEOUT,
        )

    prepared_request = requests.Request(
        method="POST",
        url=url,
        headers=headers,
        json=rtp_payload,
    ).prepare()
    body = _prepared_body(prepared_request)
    signature = sign_srtp_message(
        method=prepared_request.method,
        url=prepared_request.url,
        headers=prepared_request.headers,
        body=body,
        key_material=qsealc_key_material,
    )
    prepared_request.headers.update(signature.as_headers())

    with requests.Session() as session:
        return session.send(
            prepared_request,
            cert=(cert_path, key_path),
            timeout=HTTP_TIMEOUT,
        )


def _prepared_body(prepared_request: requests.PreparedRequest) -> bytes:
    if prepared_request.body is None:
        return b""
    if isinstance(prepared_request.body, bytes):
        return prepared_request.body
    if isinstance(prepared_request.body, str):
        return prepared_request.body.encode()
    raise TypeError("Prepared callback body must be bytes or text")
