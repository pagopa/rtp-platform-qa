import requests

from config.configuration import config

SEND_RTP_URL = config.rtp_creation_base_url_path + config.send_rtp_path
SERVICE_PROVIDER_MOCK_URL = config.mock_service_provider_url


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
        timeout=config.default_timeout
    )


def send_rtp_to_mock(rtp_payload):
    return requests.post(
        url=SERVICE_PROVIDER_MOCK_URL,
        json=rtp_payload,
        timeout=config.default_timeout
    )
