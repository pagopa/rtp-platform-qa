import uuid
import requests
import logging

from config.configuration import config

logger = logging.getLogger(__name__)

def takeover_activation(access_token: str, activation_id: str, payer_fiscal_code: str, service_provider_id: str, otp: str = None):
    """API to takeover an activation from one service provider to another
    
    :param access_token: The authentication token
    :param activation_id: The ID of the activation to takeover (or could be the OTP)
    :param payer_fiscal_code: The fiscal code of the payer
    :param service_provider_id: The new service provider ID to takeover with
    :param otp: One-Time Password (non utilizzato nella richiesta)
    :returns: the response of the call.
    :rtype: requests.Response
    """
    url_activation_id = otp if otp else activation_id
    url = config.activation_base_url_path + config.activation_by_id_path.format(activationId=url_activation_id)
    logger.info(f"Making takeover request to URL: {url}")
    
    request_id = str(uuid.uuid4())
    headers = {
        'Authorization': f'{access_token}',
        'Version': 'v1',
        'RequestId': request_id,
        'Content-Type': 'application/json'
    }
    logger.info(f"Headers: Authorization={access_token[:20]}..., RequestId={request_id}")
    
    payload = {
        'payer': {
            'fiscalCode': payer_fiscal_code,
            'rtpSpId': service_provider_id
        }
    }
    logger.info(f"Request payload: {payload}")
    
    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=config.default_timeout
    )
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    return response