import requests

from api.utils.api_version import CALLBACK_VERSION, RFC_CALLBACK_VERSION
from api.utils.endpoints import CALLBACK_URL, RFC_CALLBACK_URL
from api.utils.http_utils import HTTP_TIMEOUT


def srtp_callback(cert_path: str, key_path: str, rtp_payload, include_version_header: bool = True):
    headers = {"Version": CALLBACK_VERSION} if include_version_header else {}
    return requests.post(
        cert=(cert_path, key_path),
        url=CALLBACK_URL,
        headers=headers,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT,
    )


def srtp_rfc_callback(cert_path: str, key_path: str, rtp_payload, include_version_header: bool = True):
    """
    Send RFC (Request for Cancellation) callback.

    This is used for DS12P and DS12N callbacks which use a different endpoint
    than regular RTP callbacks.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the key file
        rtp_payload: The RFC callback payload (DS12P or DS12N)
        include_version_header: When False, omits the Version header (used for regression tests)

    Returns:
        Response object from the callback request
    """
    headers = {"Version": RFC_CALLBACK_VERSION} if include_version_header else {}
    return requests.post(
        cert=(cert_path, key_path),
        url=RFC_CALLBACK_URL,
        headers=headers,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT,
    )
