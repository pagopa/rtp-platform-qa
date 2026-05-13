import uuid

import requests

from api.utils.api_version import CANCEL_VERSION
from api.utils.endpoints import CANCEL_RTP_OPERATION, CANCEL_RTP_URL
from api.utils.http_utils import HTTP_TIMEOUT
from utils.idempotency_key_utils import generate_idempotency_key


def cancel_rtp(access_token: str, resource_id: str, reason: str):
    """
    Cancel an RTP request.

    :param access_token: Bearer access token for authorization.
    :param resource_id: UUID of the RTP resource to cancel.
    :param reason: Cancellation reason. Must be one of: PAID, MODT.
    :returns: The HTTP response.
    :rtype: requests.Response
    """
    idempotency_key = generate_idempotency_key(CANCEL_RTP_OPERATION, resource_id)

    headers = {
        "Authorization": f"{access_token}",
        "Version": CANCEL_VERSION,
        "RequestId": str(uuid.uuid4()),
        "Idempotency-key": idempotency_key,
    }

    body = {
        "resourceId": resource_id,
        "reason": reason,
    }

    return requests.post(headers=headers, url=CANCEL_RTP_URL, json=body, timeout=HTTP_TIMEOUT)
