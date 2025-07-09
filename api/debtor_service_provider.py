import uuid

import requests

from config.configuration import config


def send_srtp_to_cbi(access_token: str, rtp_payload):
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Idempotency-key': rtp_payload['resourceId'],
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.cbi_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout
    )


def send_srtp_to_poste(rtp_payload):
    return requests.post(
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Idempotency-key': rtp_payload['resourceId'],
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.poste_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout,
        verify=False
    )

def send_srtp_to_iccrea(rtp_payload):
    return requests.post(
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Idempotency-key': rtp_payload['resourceId'],
            'X-Request-ID': str(uuid.uuid4())
        },
        url=config.iccrea_send_url,
        json=rtp_payload,
        cert=(config.cert_path, config.key_path),
        timeout=config.default_timeout
    )
