import uuid
from typing import Optional

import requests

from api.utils.api_version import ACTIVATION_VERSION
from api.utils.endpoints import ACTIVATION_BY_ID_URL
from api.utils.endpoints import ACTIVATION_LIST_URL
from api.utils.endpoints import ACTIVATION_URL
from api.utils.endpoints import ACTIVATION_URL_DEV
from api.utils.http_utils import HTTP_TIMEOUT



def activate(access_token: str, payer_fiscal_code: str, service_provider_id: str):
    """API to activate a debtor to receive RTP
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        url=ACTIVATION_URL,
        headers={
            'Authorization': f'{access_token}',
            'Version': ACTIVATION_VERSION,
            'RequestId': str(uuid.uuid4())
        },
        json={
            'payer': {
                'fiscalCode': payer_fiscal_code,
                'rtpSpId': service_provider_id
            }
        },
        timeout=HTTP_TIMEOUT
    )

def activate_dev(access_token: str, payer_fiscal_code: str, service_provider_id: str):
    """API to activate a debtor to receive RTP
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        url=ACTIVATION_URL_DEV,
        headers={
            'Authorization': f'{access_token}',
            'Version': ACTIVATION_VERSION,
            'RequestId': str(uuid.uuid4())
        },
        json={
            'payer': {
                'fiscalCode': payer_fiscal_code,
                'rtpSpId': service_provider_id
            }
        },
        timeout=HTTP_TIMEOUT
    )


def get_activation_by_payer_id(access_token: str, payer_fiscal_code: str):
    """API to get activation of a debtor
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.get(
        url=ACTIVATION_URL+'/payer',
        headers={
            'Authorization': f'{access_token}',
            'Version': ACTIVATION_VERSION,
            'RequestId': str(uuid.uuid4()),
            'PayerId': payer_fiscal_code
        },
        timeout=HTTP_TIMEOUT
    )

def get_activation_by_id(access_token: str, activation_id: str):
    """API to get activation by activationId."""
    return requests.get(
        url=ACTIVATION_BY_ID_URL.format(activationId=activation_id),
        headers={
            'Authorization': f'{access_token}',
            'Version': ACTIVATION_VERSION,
            'RequestId': str(uuid.uuid4())
        },
        timeout=HTTP_TIMEOUT
    )


def get_all_activations(access_token: str, page: Optional[int] = None, size: int = 16, next_activation_id: Optional[str] = None):
    """API to list all activations.

    - Query: 'size'
    - Cursor: pass 'NextActivationId' header value to fetch the next page
    - 'page' kept for backward compatibility (if not None, it's sent)
    """
    headers = {
        'Authorization': f'{access_token}',
        'Version': ACTIVATION_VERSION,
        'RequestId': str(uuid.uuid4())
    }
    if next_activation_id:
        headers['NextActivationId'] = next_activation_id

    params = {'size': size}
    if page is not None:
        params['page'] = page

    return requests.get(
        url=ACTIVATION_LIST_URL,
        headers=headers,
        params=params,
        timeout=HTTP_TIMEOUT
    )
