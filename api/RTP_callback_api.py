import requests

from api.utils.api_version import CALLBACK_VERSION
from api.utils.endpoints import CALLBACK_URL
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
