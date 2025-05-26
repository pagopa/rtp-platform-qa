import uuid

import allure
import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.deactivation import deactivate
from config.configuration import secrets
from utils.dataset import fake_fc


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('A debtor is deactivated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.happy_path
def test_deactivate_debtor():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )

    debtor_fc = fake_fc()
    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor'

    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]

    deactivation_response = deactivate(access_token, activation_id)
    assert deactivation_response.status_code == 204, f'Error deactivating debtor, expected 204 but got {deactivation_response.status_code}'


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('Deactivation fails for non-existing activation')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.unhappy_path
def test_deactivate_nonexistent_debtor():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )

    fake_activation_id = str(uuid.uuid4())

    deactivation_response = deactivate(access_token, fake_activation_id)
    assert deactivation_response.status_code == 404, f'Expected 404 status code for non-existent activation, got {deactivation_response.status_code}'


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('Deactivation fails for activation by another service provider')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.unhappy_path
def test_deactivate_debtor_wrong_service_provider():
    debtor_service_provider_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )

    debtor_service_provider_B_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token
    )

    debtor_fc = fake_fc()
    activation_response = activate(
        debtor_service_provider_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor'

    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]

    deactivation_response = deactivate(debtor_service_provider_B_token, activation_id)
    assert deactivation_response.status_code == 404, f'Expected 404 for deactivation by wrong service provider, got {deactivation_response.status_code}'
