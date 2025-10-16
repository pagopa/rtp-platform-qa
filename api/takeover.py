import uuid

import requests

from config.configuration import config

def takeover_activation(access_token: str, payer_fiscal_code: str, service_provider_id: str, otp: str) -> requests.Response:
    """API to takeover an activation from one service provider to another

    :param access_token: The authentication token
    :param payer_fiscal_code: The fiscal code of the payer
    :param service_provider_id: The new service provider ID to takeover with
    :param otp: One-Time Password for verification (required)
    :returns: the response of the call.
    :rtype: requests.Response
    """
    if not otp:
        raise ValueError('OTP is required for takeover')

    url = f"{config.activation_base_url_path}/activations/takeover/{otp}"
    request_id = str(uuid.uuid4())
    headers = {
        'Authorization': f'{access_token}',
        'Version': 'v1',
        'RequestId': request_id,
        'Content-Type': 'application/json'
    }

    payload = {
        'payer': {
            'fiscalCode': payer_fiscal_code,
            'rtpSpId': service_provider_id
        }
    }

    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=config.default_timeout
    )

    return response
