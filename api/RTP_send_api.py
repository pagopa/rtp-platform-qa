import uuid

import requests

from api.utils.endpoints import SEND_RTP_URL, SERVICE_PROVIDER_MOCK_URL, STATUS_UPDATE_RTP_URL
from api.utils.http_utils import HTTP_TIMEOUT


def _post_rtp(access_token: str, rtp_payload: dict, version: str) -> requests.Response:
    return requests.post(
        headers={"Authorization": f"{access_token}", "Version": version},
        url=SEND_RTP_URL,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT,
    )


def send_rtp(access_token: str, rtp_payload: dict) -> requests.Response:
    """API to post a rtp request (Version: v1).
    :returns: the response of the call.
    :rtype: requests.Response
    """
    return _post_rtp(access_token, rtp_payload, "v1")


def send_rtp_v2(access_token: str, rtp_payload: dict) -> requests.Response:
    """API to post a rtp request (Version: v2).
    :returns: the response of the call.
    :rtype: requests.Response
    """
    return _post_rtp(access_token, rtp_payload, "v2")


def _post_status_update(
    access_token: str,
    status_update_payload: dict,
    version: str,
) -> requests.Response:
    return requests.post(
        headers={
            "Authorization": f"{access_token}",
            "Version": version,
            "RequestId": str(uuid.uuid4()),
        },
        url=STATUS_UPDATE_RTP_URL,
        json=status_update_payload,
        timeout=HTTP_TIMEOUT,
    )


def status_update_rtp_v2(
    access_token: str,
    status_update_payload: dict,
) -> requests.Response:
    """Post an RTP status-update request (Version: v2).
    :returns: the response of the call.
    :rtype: requests.Response
    """
    return _post_status_update(access_token, status_update_payload, "v2")


def send_rtp_to_mock(rtp_payload):
    return requests.post(url=SERVICE_PROVIDER_MOCK_URL, json=rtp_payload, timeout=HTTP_TIMEOUT)
