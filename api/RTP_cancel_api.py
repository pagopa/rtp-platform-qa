import uuid

import requests

from .debtor_service_provider_api import generate_idempotency_key
from api.utils.api_version import CANCEL_VERSION
from api.utils.endpoints import CANCEL_RTP_OPERATION
from api.utils.endpoints import CANCEL_RTP_URL
from api.utils.http_utils import HTTP_TIMEOUT




def cancel_rtp(access_token: str, rtp_id: str):
    url = CANCEL_RTP_URL.format(rtp_id=rtp_id)
    idempotency_key = generate_idempotency_key(CANCEL_RTP_OPERATION, rtp_id)

    headers = {
        'Authorization': f'{access_token}',
        'Version': CANCEL_VERSION,
        'RequestId': str(uuid.uuid4()),
        'Idempotency-key': idempotency_key
    }

    return requests.post(
        headers=headers,
        url=url,
        timeout=HTTP_TIMEOUT
    )
