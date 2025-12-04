import uuid

import allure
import pytest

from api.activation import activate
from api.deactivation import deactivate
from config.configuration import secrets


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('A debtor is deactivated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.happy_path
def test_deactivate_debtor(debtor_service_provider_token_a, random_fiscal_code):

    activation_response = activate(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor'

    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]

    deactivation_response = deactivate(debtor_service_provider_token_a, activation_id)
    assert deactivation_response.status_code == 204, f'Error deactivating debtor, expected 204 but got {deactivation_response.status_code}'


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('Deactivation fails for non-existing activation')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.unhappy_path
def test_deactivate_nonexistent_debtor(debtor_service_provider_token_a):

    fake_activation_id = str(uuid.uuid4())

    deactivation_response = deactivate(debtor_service_provider_token_a, fake_activation_id)
    assert deactivation_response.status_code == 404, f'Expected 404 status code for non-existent activation, got {deactivation_response.status_code}'


@allure.feature('Deactivation')
@allure.story('Debtor deactivation')
@allure.title('Deactivation fails for activation by another service provider')
@pytest.mark.auth
@pytest.mark.deactivation
@pytest.mark.unhappy_path
def test_deactivate_debtor_wrong_service_provider(debtor_service_provider_token_a, debtor_service_provider_token_b, random_fiscal_code):

    activation_response = activate(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor'

    location = activation_response.headers['Location']
    activation_id = location.split('/')[-1]

    deactivation_response = deactivate(debtor_service_provider_token_b, activation_id)
    assert deactivation_response.status_code == 404, f'Expected 404 for deactivation by wrong service provider, got {deactivation_response.status_code}'
