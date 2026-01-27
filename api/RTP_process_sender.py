import uuid

import requests

from api.utils.api_version import SEND_GPD_MESSAGE_VERSION
from api.utils.endpoints import RTP_SENDER_GPD_MESSAGE_URL
from api.utils.http_utils import HTTP_TIMEOUT
from utils.idempotency_key_utils import generate_idempotency_key


def send_gpd_message(access_token: str, message_payload: dict):
    """Send an RTP message to the GPD sender service.
    
    :param access_token: Bearer token for RTP Consumer client
    :param message_payload: RTP message payload (CREATE/UPDATE/DELETE operation)
    :returns: The response of the call
    :rtype: requests.Response
    """
    
    msg_id = str(message_payload.get('id', ''))
    resource_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, msg_id))
    
    operation = message_payload.get('operation', 'CREATE')
    
    idempotency_key = generate_idempotency_key(operation, resource_uuid)
    
    headers = {
        'Authorization': f'{access_token}',
        'Version': SEND_GPD_MESSAGE_VERSION,
        'RequestId': str(uuid.uuid4()),
        'Idempotency-Key': idempotency_key
    }
    
    return requests.post(
        headers=headers,
        url=RTP_SENDER_GPD_MESSAGE_URL,
        json=message_payload,
        timeout=HTTP_TIMEOUT
    )
