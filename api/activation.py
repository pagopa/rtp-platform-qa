import uuid
import requests

from config.configuration import config

ACTIVATION_URL = config.activation_base_url_path + config.activation_path
ACTIVATION_LIST_URL = config.activation_base_url_path + config.activation_list_path


def activate(access_token: str, payer_fiscal_code: str, service_provider_id: str):
    """API to activate a debtor to receive RTP
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        url=ACTIVATION_URL,
        headers={
            'Authorization': f'{access_token}',
            'Version': 'v1',
            'RequestId': str(uuid.uuid4())
        },
        json={
            'payer': {
                'fiscalCode': payer_fiscal_code,
                'rtpSpId': service_provider_id
            }
        },
        timeout=config.default_timeout
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
            'Version': 'v1',
            'RequestId': str(uuid.uuid4()),
            'PayerId': payer_fiscal_code
        },
        timeout=config.default_timeout
    )


def get_all_activations(access_token: str, page: int = 0, size: int = 16):
    """API to list all activations with pagination."""
    return requests.get(
        url=ACTIVATION_LIST_URL,
        headers={
            'Authorization': f'{access_token}',
            'Version': 'v1',
            'RequestId': str(uuid.uuid4())
        },
        params={'page': page, 'size': size},
        timeout=config.default_timeout
    )


