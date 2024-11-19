import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import secrets


@pytest.mark.auth
def test_get_valid_token():
    token = get_valid_access_token(client_id=secrets.client_id, client_secret=secrets.client_secret)

    assert isinstance(token, str), 'Token must be a string'
    assert token.startswith('Bearer '), "Token must start with 'Bearer '"
    assert len(token) > 7, "Token should not be empty after 'Bearer '"


@pytest.mark.auth
def test_get_token_with_invalid_client_id():
    invalid_client_id = '00000000-0000-0000-0000-000000000000'
    token_response = get_access_token(client_id=invalid_client_id,
                                      client_secret=secrets.client_secret)
    assert token_response.status_code == 401
    assert f'Client {invalid_client_id} not found' in str(token_response.json()['descriptions'])


@pytest.mark.auth
def test_get_token_with_invalid_client_secret():
    invalid_client_secret = '000000000000000000000000000000000000'
    token_response = get_access_token(client_id=secrets.client_id,
                                      client_secret=invalid_client_secret)
    assert token_response.status_code == 401
    assert 'Wrong secret' in str(token_response.json()['descriptions'])
