import requests

from config.configuration import config


def srtp_callback(cert_path: str, key_path: str, rtp_payload, certificate_serial: str):
    return requests.post(
        cert=(
            cert_path,
            key_path
        ),
        url=config.callback_url,
        headers={
            'Version': config.callback_api_version,
            'X-certificate-client-Serial': certificate_serial,
        },
        json=rtp_payload,
        timeout=config.default_timeout
    )
