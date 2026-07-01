import requests

from api.utils.endpoints import SEND_RTP_URL, SERVICE_PROVIDER_MOCK_URL
from api.utils.http_utils import HTTP_TIMEOUT


def _post_rtp(access_token: str, rtp_payload, version: str) -> requests.Response:
    return requests.post(
        headers={"Authorization": f"{access_token}", "Version": version},
        url=SEND_RTP_URL,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT,
    )


def send_rtp(access_token: str, rtp_payload):
    """API to post a rtp request (Version: v1).
    :returns: the response of the call.
    :rtype: requests.Response
    """
    return _post_rtp(access_token, rtp_payload, "v1")


def send_rtp_v2(access_token: str, rtp_payload):
    """API to post a rtp request (Version: v2).
    :returns: the response of the call.
    :rtype: requests.Response
    """
    return _post_rtp(access_token, rtp_payload, "v2")


def send_rtp_to_mock(rtp_payload):
    return requests.post(url=SERVICE_PROVIDER_MOCK_URL, json=rtp_payload, timeout=HTTP_TIMEOUT)
