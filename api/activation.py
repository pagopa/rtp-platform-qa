import uuid

import requests

from config.configuration import config

ACTIVATION_URL = config.activation_base_url_path + config.activation_path


def activate(access_token: str, payer_fiscal_code: str, service_provider_id: str):
    """API to activate a debtor in RTP
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
