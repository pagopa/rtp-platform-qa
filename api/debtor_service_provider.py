import uuid

import requests

from config.configuration import config


def send_srtp_to_cbi(access_token: str, rtp_payload):
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Idempotency-key;': rtp_payload['resourceId'],
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.cbi_send_url,
        json=rtp_payload,
        timeout=config.default_timeout
    )
