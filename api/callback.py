import requests

from config.configuration import config


def srtp_callback(cert_path: str, key_path: str, rtp_payload):
    return requests.post(
        cert=(
            cert_path,
            key_path
        ),
        url=config.callback_url,
        headers={
            'Version': 'v1'
        },
        json=rtp_payload,
        timeout=config.default_timeout
    )
