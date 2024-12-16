import requests

from config.configuration import config

SEND_RTP_URL = config.rtp_creation_base_url_path + config.send_rtp_path


def send_rtp(access_token: str, rtp_payload):
    """API to post a rtp request
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
        },
        url=SEND_RTP_URL,
        json=rtp_payload,
        timeout=config.default_timeout
    )
