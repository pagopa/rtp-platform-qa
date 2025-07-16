import uuid

import requests

from config.configuration import config
from utils.idempotency import generate_idempotency_key


CREATE_RTP_OPERATION = '/sepa-request-to-pay-requests'


def send_srtp_to_cbi(access_token: str, rtp_payload):
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.cbi_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout
    )


def send_srtp_to_poste(rtp_payload):
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.poste_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout,
        verify=False
    )


def send_srtp_to_iccrea(rtp_payload):
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.iccrea_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout
    )
