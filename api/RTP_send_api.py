import requests

from api.utils.endpoints import SEND_RTP_URL
from api.utils.endpoints import SERVICE_PROVIDER_MOCK_URL
from api.utils.http_utils import HTTP_TIMEOUT


def send_rtp(access_token: str, rtp_payload):
    """API to post a rtp request
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Version': 'v1'
        },
        url=SEND_RTP_URL,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT
    )


def send_rtp_to_mock(rtp_payload):
    return requests.post(
        url=SERVICE_PROVIDER_MOCK_URL,
        json=rtp_payload,
        timeout=HTTP_TIMEOUT
    )
