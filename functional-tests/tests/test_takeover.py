import time

import allure
import pytest

from api.activation import activate
from api.activation import get_activation_by_id
from api.activation import get_activation_by_payer_id
from api.auth import get_access_token
from api.auth import get_valid_access_token
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

    token_a = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    activation_response = activate(token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id)
    assert activation_response.status_code == 201, f"Failed to activate user with service provider A: {activation_response.text}"

    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]
    assert activation_id is not None, 'Activation ID is missing in Location header'

    get_response = get_activation_by_payer_id(token_a, random_fiscal_code)
    assert get_response.status_code == 200, f"Failed to get user activation: {get_response.text}"

    current_sp = get_response.json()['payer']['rtpSpId']
    assert current_sp == secrets.debtor_service_provider.service_provider_id, f"Expected service provider {secrets.debtor_service_provider.service_provider_id}, got {current_sp}"

    token_b = get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token
    )

    second_activation_response = activate(token_b, random_fiscal_code, secrets.debtor_service_provider_B.service_provider_id)
    assert second_activation_response.status_code == 409, f"Expected 409 conflict, got {second_activation_response.status_code}"

    location_header = second_activation_response.headers.get('Location')
    assert location_header is not None, 'Missing Location header in 409 response'

    otp = location_header.split('/')[-1]

    takeover_response = takeover_activation(
        token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp
    )

    assert takeover_response.status_code == 201, f"Failed to takeover: {takeover_response.text}"

    new_location = takeover_response.headers.get('Location')
    assert new_location is not None, 'Missing Location header in takeover response'
    new_activation_id = new_location.split('/')[-1]

    time.sleep(1)

    get_after_takeover = get_activation_by_id(token_b, new_activation_id)
    assert get_after_takeover.status_code == 200, f"Failed to get activation after takeover: {get_after_takeover.text}"

    new_sp = get_after_takeover.json()['payer']['rtpSpId']
    assert new_sp == secrets.debtor_service_provider_B.service_provider_id, f"Takeover failed. Expected service provider {secrets.debtor_service_provider_B.service_provider_id}, got {new_sp}"
