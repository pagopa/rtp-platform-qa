import uuid
from typing import Optional

import requests

from api.utils.api_version import TAKEOVER_API_VERSION
from api.utils.endpoints import TAKEOVER_NOTIFICATION_URL
from api.utils.endpoints import TAKEOVER_URL
from api.utils.http_utils import APPLICATION_JSON_HEADER
from api.utils.http_utils import HTTP_TIMEOUT

def takeover_activation(
    access_token: str,
    payer_fiscal_code: str,
    service_provider_id: str,
    otp: str,
    include_payload: bool = False,
) -> requests.Response:
    """API to takeover an activation from one service provider to another

    :param access_token: The authentication token
    :param payer_fiscal_code: The fiscal code of the payer
    :param service_provider_id: The new service provider ID to takeover with
    :param otp: One-Time Password for verification (required)
    :param include_payload: If True, send body payload with payer data
    :returns: the response of the call.
    :rtype: requests.Response
    """
    if not otp:
        raise ValueError('OTP is required for takeover')


    request_id = str(uuid.uuid4())
    headers = {
        'Authorization': f'{access_token}',
        'Version': TAKEOVER_API_VERSION,
        'RequestId': request_id,
        **APPLICATION_JSON_HEADER
    }

    payload = None
    if include_payload:
        payload = {
            'payer': {
                'fiscalCode': payer_fiscal_code,
                'rtpSpId': service_provider_id
            }
        }

    response = requests.post(
        url=f"{TAKEOVER_URL}/{otp}",
        headers=headers,
        json=payload,
        timeout=HTTP_TIMEOUT
    )

    return response


def send_takeover_notification(old_activation_id: str, fiscal_code: str, takeover_timestamp: str, request_id: Optional[str] = None) -> requests.Response:
    """Send takeover notification to mock endpoint (UAT only)"""

    headers = {
        **APPLICATION_JSON_HEADER,
        'X-Request-Id': request_id or str(uuid.uuid4()),
        'X-Version': TAKEOVER_API_VERSION
    }
    payload = {
        'oldActivationId': old_activation_id,
        'fiscalCode': fiscal_code,
        'takeoverTimestamp': takeover_timestamp
    }
    response = requests.post(
        url=TAKEOVER_NOTIFICATION_URL,
        headers=headers,
        json=payload,
        timeout=HTTP_TIMEOUT
    )
    return response
