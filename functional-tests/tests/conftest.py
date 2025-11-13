from types import SimpleNamespace

import pytest

from api.activation import activate
from api.activation import activate_dev
from api.auth import get_access_token
from api.auth import get_access_token_dev
from api.auth import get_valid_access_token
from api.debt_position import create_debt_position
from api.debt_position import delete_debt_position
from api.debt_position import get_debt_position
from api.debt_position import update_debt_position
from config.configuration import secrets
from utils.dataset import fake_fc
from utils.dataset import generate_iupd
from utils.extract_next_activation_id import extract_next_activation_id
from utils.generators import generate_iuv

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

@pytest.fixture(
    params=[
        {'name': 'UAT', 'is_dev': False},
        {'name': 'DEV', 'is_dev': True}
    ],
    ids=['environment_uat', 'environment_dev']
)
def environment(request):
    """Fixture to provide environment-specific configurations."""
    env = request.param
    is_dev = env['is_dev']

    env.update({
        'create_function': lambda sk, org_id, payload, to_publish: create_debt_position(sk, org_id, payload, to_publish, is_dev),
        'get_function': lambda sk, org_id, iupd: get_debt_position(sk, org_id, iupd, is_dev),
        'delete_function': lambda sk, org_id, iupd: delete_debt_position(sk, org_id, iupd, is_dev),
        'update_function': lambda sk, org_id, iupd, payload, to_publish=True: update_debt_position(sk, org_id, iupd, payload, to_publish, is_dev),
        'subscription_key': secrets.debt_positions_dev.subscription_key if is_dev else secrets.debt_positions.subscription_key,
        'organization_id': secrets.debt_positions_dev.organization_id if is_dev else secrets.debt_positions.organization_id
    })

    return env

@pytest.fixture
def setup_data(environment):
    """Fixture to set up data for tests based on the environment."""
    access_token_function = get_access_token_dev if environment['is_dev'] else get_access_token

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=access_token_function
    )

    debtor_fc = fake_fc()

    activation_function = activate_dev if environment['is_dev'] else activate

    activation_response = activation_function(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor before creating debt position'

    iupd = generate_iupd()
    iuv = generate_iuv()

    return {
        'debtor_fc': debtor_fc,
        'iupd': iupd,
        'iuv': iuv,
        'subscription_key': environment['subscription_key'],
        'organization_id': environment['organization_id'],
    }

@pytest.fixture
def gpd_test_data(setup_data):
    """Fixture to provide GPD test data with attribute access."""
    return SimpleNamespace(**setup_data)
