import pytest
import uuid
import allure
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.auth import get_valid_access_token, get_access_token
from api.activation import activate, get_activation_by_payer_id, get_activation_by_id
from api.takeover import takeover_activation
from config.configuration import secrets
from utils.dataset import fake_fc

@pytest.fixture
def random_fiscal_code():
    """Generate a random fiscal code for testing"""
    return fake_fc()

@allure.feature('Activation')
@allure.story('Takeover')
@pytest.mark.functional
def test_takeover_flow(random_fiscal_code):
    """Test the takeover flow where a user changes service provider"""
    logger.info(f"Starting takeover test with fiscal code: {random_fiscal_code}")
    
    token_a = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    logger.info(f"Got token for service provider A: {token_a[:20]}...")
    
    activation_response = activate(token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id)
    assert activation_response.status_code == 201, f"Failed to activate user with service provider A: {activation_response.text}"
    
    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]
    logger.info(f"Activation ID: {activation_id}")
    assert activation_id is not None, "Activation ID is missing in Location header"
    
    get_response = get_activation_by_payer_id(token_a, random_fiscal_code)
    assert get_response.status_code == 200, f"Failed to get user activation: {get_response.text}"
    
    current_sp = get_response.json()['payer']['rtpSpId']
    logger.info(f"Current service provider: {current_sp}")
    assert current_sp == secrets.debtor_service_provider.service_provider_id, f"Expected service provider {secrets.debtor_service_provider.service_provider_id}, got {current_sp}"
    
    token_b = get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token
    )
    logger.info(f"Got token for service provider B: {token_b[:20]}...")
    
    second_activation_response = activate(token_b, random_fiscal_code, secrets.debtor_service_provider_B.service_provider_id)
    logger.info(f"Second activation response status: {second_activation_response.status_code}")
    assert second_activation_response.status_code == 409, f"Expected 409 conflict, got {second_activation_response.status_code}"
    
    location_header = second_activation_response.headers.get('Location')
    logger.info(f"Location header: {location_header}")
    assert location_header is not None, "Missing Location header in 409 response"
    
    otp = location_header.split('/')[-1]
    logger.info(f"Extracted OTP: {otp}")
    
    logger.info(f"Attempting takeover with OTP as activation_id: {otp}")
    takeover_response = takeover_activation(
        token_b,
        activation_id,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp
    )
    
    logger.info(f"Takeover response status: {takeover_response.status_code}")
    if takeover_response.text:
        logger.info(f"Takeover response body: {takeover_response.text}")
    
    assert takeover_response.status_code == 201, f"Failed to takeover: {takeover_response.text}"
    
    new_location = takeover_response.headers.get('Location')
    assert new_location is not None, "Missing Location header in takeover response"
    new_activation_id = new_location.split('/')[-1]
    logger.info(f"New activation ID after takeover: {new_activation_id}")
    
    time.sleep(1)
    
    get_after_takeover = get_activation_by_id(token_b, new_activation_id)
    assert get_after_takeover.status_code == 200, f"Failed to get activation after takeover: {get_after_takeover.text}"
    
    new_sp = get_after_takeover.json()['payer']['rtpSpId']
    logger.info(f"New service provider after takeover: {new_sp}")
    assert new_sp == secrets.debtor_service_provider_B.service_provider_id, f"Takeover failed. Expected service provider {secrets.debtor_service_provider_B.service_provider_id}, got {new_sp}"