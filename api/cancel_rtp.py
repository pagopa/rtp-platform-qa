import requests

from config.configuration import config

CANCEL_RTP_URL = config.rtp_creation_base_url_path + config.cancel_rtp_path


def cancel_rtp(access_token: str, rtp_id: str):
    url = CANCEL_RTP_URL.format(rtp_id=rtp_id)

    headers = {
        'Authorization': f'{access_token}',
        'Version': config.cancel_api_version
    }

    return requests.post(
        headers=headers,
        url=url,
        timeout=config.cancel_api_timeout
    )
