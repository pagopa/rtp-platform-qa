import uuid

import requests

from api.utils.endpoints import CBI_SEND_URL
from api.utils.endpoints import CREATE_RTP_OPERATION
from api.utils.endpoints import ICCREA_SEND_URL
from api.utils.endpoints import POSTE_SEND_URL
from api.utils.http_utils import CERT_PATH
from api.utils.http_utils import HTTP_TIMEOUT
from api.utils.http_utils import KEY_PATH
from config.configuration import config
from utils.idempotency_key_utils import generate_idempotency_key
from utils.type_utils import JsonType


def send_srtp_to_cbi(access_token: str, rtp_payload):
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=CBI_SEND_URL,
        json=rtp_payload,
        cert=(CERT_PATH, KEY_PATH),
        timeout=HTTP_TIMEOUT
    )


def send_srtp_to_poste(access_token: str, rtp_payload: JsonType):
    """
    Sends an RTP payload to the POSTE endpoint.

    :param access_token: Bearer access token for authorization.
    :type access_token: str
    :param rtp_payload: RTP payload in JSON format.
    :type rtp_payload: JsonType
    """
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=POSTE_SEND_URL,
        json=rtp_payload,
        cert=(CERT_PATH, KEY_PATH),
        timeout=HTTP_TIMEOUT,
        verify=False
    )


def send_srtp_to_iccrea(rtp_payload):
    idempotency_key = generate_idempotency_key(CREATE_RTP_OPERATION, rtp_payload['resourceId'])
    return requests.post(
        headers={
            'Idempotency-key': idempotency_key,
            'X-Request-ID': str(uuid.uuid4())
        },
        url=ICCREA_SEND_URL,
        json=rtp_payload,
        cert=(CERT_PATH, KEY_PATH),
        timeout=HTTP_TIMEOUT,
    )
