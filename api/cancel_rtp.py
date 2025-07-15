import uuid

import requests

from .debtor_service_provider import generate_idempotency_key
from config.configuration import config

CANCEL_RTP_OPERATION = '/cancel'

CANCEL_RTP_URL = config.rtp_creation_base_url_path + config.cancel_rtp_path


def cancel_rtp(access_token: str, rtp_id: str):
    url = CANCEL_RTP_URL.format(rtp_id=rtp_id)
    idempotency_key = generate_idempotency_key(CANCEL_RTP_OPERATION, rtp_id)

    headers = {
        'Authorization': f'{access_token}',
        'Version': config.cancel_api_version,
        'RequestId': str(uuid.uuid4()),
        'Idempotency-key': idempotency_key
    }

    return requests.post(
        headers=headers,
        url=url,
        timeout=config.default_timeout
    )
