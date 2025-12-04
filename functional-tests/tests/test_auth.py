import allure
import pytest

from api.auth import get_access_token
from config.configuration import secrets


@allure.feature('Authentication')
@allure.story('Service Provider authentication')
@allure.title('A Service Provider is authenticated')
@pytest.mark.auth
@pytest.mark.happy_path
def test_get_valid_token(debtor_service_provider_token_a):

    assert isinstance(debtor_service_provider_token_a, str), 'Token must be a string'
    assert debtor_service_provider_token_a.startswith('Bearer '), "Token must start with 'Bearer '"
    assert len(debtor_service_provider_token_a) > 7, "Token should not be empty after 'Bearer '"


@allure.feature('Authentication')
@allure.story('Service Provider authentication')
@allure.title('A Service Provider with invalid client ID is not authenticated')
@pytest.mark.auth
@pytest.mark.unhappy_path
def test_get_token_with_invalid_client_id():

    invalid_client_id = '00000000-0000-0000-0000-000000000000'
    token_response = get_access_token(client_id=invalid_client_id,
                                      client_secret=secrets.creditor_service_provider.client_secret)
    assert token_response.status_code == 401
    assert f'Client {invalid_client_id} not found' in str(token_response.json()['descriptions'])


@allure.feature('Authentication')
@allure.story('Service Provider authenticated')
@allure.title('A Service Provider with invalid client secret is not authenticated')
@pytest.mark.auth
@pytest.mark.unhappy_path
def test_get_token_with_invalid_client_secret():
    
    invalid_client_secret = '000000000000000000000000000000000000'
    token_response = get_access_token(client_id=secrets.creditor_service_provider.client_id,
                                      client_secret=invalid_client_secret)
    assert token_response.status_code == 401
