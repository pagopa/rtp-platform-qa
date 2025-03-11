import requests

from config.configuration import config


def srtp_callback(rtp_payload):
    return requests.post(
        url=config.callback_url,
        json=rtp_payload,
        timeout=config.default_timeout
    )
