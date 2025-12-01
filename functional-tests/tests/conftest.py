import re
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


# ============================================================
#  Logging / reporting utilities (sanitize Bearer tokens)
# ============================================================
def sanitize_bearer_token(text):
    """Remove bearer tokens from text to prevent exposure in reports."""
    if not text or not isinstance(text, str):
        return text

    pattern = r'Bearer\s+[A-Za-z0-9_\-\.]{50,}'
    return re.sub(pattern, 'Bearer ***REDACTED***', text)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook to post-process test reports:
    - removes bearer tokens from longrepr
    - sanitizes parametrized values that contain Bearer tokens
    """
    outcome = yield
    report = outcome.get_result()

    if report.longrepr:
        report.longrepr = sanitize_bearer_token(str(report.longrepr))

    if hasattr(item, 'callspec') and hasattr(item.callspec, 'params'):
        for key, value in item.callspec.params.items():
            if isinstance(value, str) and 'Bearer' in value:
                item.callspec.params[key] = sanitize_bearer_token(value)


# ============================================================
#  Access token fixtures for Debtor Service Providers
# ============================================================

@pytest.fixture
def debtor_service_provider_token_a() -> str:
    """
    Access token for Debtor Service Provider A.
    Used by tests that act as the primary RTP SP.
    """
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )


@pytest.fixture
def debtor_service_provider_token_b() -> str:
    """
    Access token for Debtor Service Provider B.
    Used mainly in takeover / multi-SP scenarios.
    """
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token,
    )


# ============================================================
#  Activation fixtures (create activation, cursor helpers)
# ============================================================
@pytest.fixture
def make_activation(debtor_service_provider_token_a):
    """
    Factory fixture:
    creates a debtor activation and returns (activation_id, debtor_fc).
    """
    def _create():
        debtor_fc = fake_fc()
        res = activate(
            debtor_service_provider_token_a,
            debtor_fc,
            secrets.debtor_service_provider.service_provider_id,
        )
        assert res.status_code == 201, f'Activation failed: {res.status_code} {res.text}'
        activation_id = res.headers['Location'].rstrip('/').split('/')[-1]
        return activation_id, debtor_fc

    return _create


@pytest.fixture
def next_cursor():
    """
    Helper used in activation listing tests to extract the next activation id
    (cursor) from API responses.
    """
    return extract_next_activation_id


@pytest.fixture
def random_fiscal_code():
    """Generate a random fiscal code for tests that need a fresh debtor."""
    return fake_fc()


# ============================================================
#  Environment fixture (UAT / DEV) + Debt Position helpers
# ============================================================
@pytest.fixture(
    params=[
        {'name': 'UAT', 'is_dev': False},
        {'name': 'DEV', 'is_dev': True},
    ],
    ids=['environment_uat', 'environment_dev'],
)
def environment(request):
    """
    Parametrized environment fixture.

    For each test run it yields:
    - name: logical name (UAT / DEV)
    - is_dev: bool flag (True for DEV)
    - create_function / get_function / delete_function / update_function:
      bound callables for Debt Position API, already configured for the env
    - subscription_key, organization_id: env-specific settings
    """
    env = request.param
    is_dev = env['is_dev']

    env.update({
        'create_function': lambda sk, org_id, payload, to_publish: create_debt_position(
            sk, org_id, payload, to_publish, is_dev
        ),
        'get_function': lambda sk, org_id, iupd: get_debt_position(
            sk, org_id, iupd, is_dev
        ),
        'delete_function': lambda sk, org_id, iupd: delete_debt_position(
            sk, org_id, iupd, is_dev
        ),
        'update_function': lambda sk, org_id, iupd, payload, to_publish=True: update_debt_position(
            sk, org_id, iupd, payload, to_publish, is_dev
        ),
        'subscription_key': (
            secrets.debt_positions_dev.subscription_key
            if is_dev
            else secrets.debt_positions.subscription_key
        ),
        'organization_id': (
            secrets.debt_positions_dev.organization_id
            if is_dev
            else secrets.debt_positions.organization_id
        ),
    })

    return env


# ============================================================
#  GPD data setup fixtures (Debt Position preconditions)
# ============================================================
@pytest.fixture
def setup_data(environment):
    """
    Prepare base test data for GPD / debt position tests:

    - resolves the correct access_token function (UAT vs DEV)
    - activates a debtor (precondition for creating debt positions)
    - generates synthetic IUPD and IUV
    - exposes env-specific subscription key and organization id
    """
    access_token_function = (
        get_access_token_dev if environment['is_dev'] else get_access_token
    )

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=access_token_function,
    )

    debtor_fc = fake_fc()

    activation_function = activate_dev if environment['is_dev'] else activate

    activation_response = activation_function(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, (
        'Error activating debtor before creating debt position'
    )

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
    """
    Convenience wrapper over setup_data that exposes fields as attributes:
    e.g. gpd_test_data.debtor_fc, gpd_test_data.iupd, …
    """
    return SimpleNamespace(**setup_data)
