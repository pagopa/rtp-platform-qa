import pytest

from api.auth import get_valid_token
from config.configuration import secrets


@pytest.mark.auth
def test_get_valid_token():
    token = get_valid_token(client_id=secrets.client_id, client_secret=secrets.client_secret)

    assert isinstance(token, str), 'Token must be a string'
    assert token.startswith('Bearer '), "Token must start with 'Bearer '"
    assert len(token) > 7, "Token should not be empty after 'Bearer '"
