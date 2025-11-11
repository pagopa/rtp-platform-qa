import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import secrets
from utils.dataset import fake_fc
from utils.extract_next_activation_id import extract_next_activation_id


@pytest.fixture
def access_token():
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

@pytest.fixture
def make_activation(access_token):
    """
    Create a debtor activation and return (activation_id, debtor_fc).
    """
    def _create():
        debtor_fc = fake_fc()
        res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
        assert res.status_code == 201, f'Activation failed: {res.status_code} {res.text}'
        activation_id = res.headers['Location'].rstrip('/').split('/')[-1]
        return activation_id, debtor_fc
    return _create


@pytest.fixture
def next_cursor():
    return extract_next_activation_id

@pytest.fixture
def random_fiscal_code():
    """Generate a random fiscal code for testing"""
    return fake_fc()

@pytest.fixture
def token_a() -> str:
    """Access token for the debtor service provider A"""
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )

@pytest.fixture
def token_b() -> str:
    """Access token for the debtor service provider B"""
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token
    )
