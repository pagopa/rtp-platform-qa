import requests

from api.utils.api_version import CALLBACK_VERSION
from api.utils.endpoints import CALLBACK_URL, RFC_CALLBACK_URL
from api.utils.http_utils import HTTP_TIMEOUT


def srtp_callback(cert_path: str, key_path: str, rtp_payload):
    return requests.post(
        cert=(
            cert_path,
            key_path
        ),
        url=CALLBACK_URL,
        headers={
            'Version': CALLBACK_VERSION
        },
        json=rtp_payload,
        timeout=HTTP_TIMEOUT
    )


def srtp_rfc_callback(cert_path: str, key_path: str, rtp_payload):
    """
    Send RFC (Request for Cancellation) callback.

    This is used for DS12P and DS12N callbacks which use a different endpoint
    than regular RTP callbacks.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the key file
        rtp_payload: The RFC callback payload (DS12P or DS12N)

    Returns:
        Response object from the callback request
    """
    return requests.post(
        cert=(
            cert_path,
            key_path
        ),
        url=RFC_CALLBACK_URL,
        headers={
            'Version': CALLBACK_VERSION
        },
        json=rtp_payload,
        timeout=HTTP_TIMEOUT
    )
