from types import SimpleNamespace
from typing import Callable
from typing import Dict
from typing import Generator
from typing import Mapping
from typing import MutableMapping
from typing import Optional
from typing import Tuple

import pytest
from _pytest.fixtures import SubRequest
from _pytest.nodes import Item
from _pytest.reports import TestReport

from api.auth_api import get_access_token
from api.auth_api import get_valid_access_token
from api.debtor_activation_api import activate
from api.GPD_debt_position_api import create_debt_position
from api.GPD_debt_position_api import delete_debt_position
from api.GPD_debt_position_api import get_debt_position
from api.GPD_debt_position_api import update_debt_position
from config.configuration import config
from config.configuration import secrets
from utils.cryptography_utils import pfx_to_pem
from utils.extract_next_activation_id import extract_next_activation_id
from utils.fiscal_code_utils import fake_fc
from utils.generators_utils import generate_iupd
from utils.generators_utils import generate_iuv
from utils.log_sanitizer_helper import sanitize_bearer_token

# ============================================================
#  Logging / reporting utilities (sanitize Bearer tokens)
# ============================================================


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: Item,
) -> Generator[None, None, None]:
    """
    Pytest hook to post-process test reports:
    - removes bearer tokens from longrepr
    - sanitizes parametrized values that contain Bearer tokens
    """
    outcome = yield
    report: TestReport = outcome.get_result()

    if report.longrepr:
        report.longrepr = sanitize_bearer_token(str(report.longrepr))

    if hasattr(item, 'callspec') and hasattr(item.callspec, 'params'):
        params: MutableMapping[str, object] = item.callspec.params
        for key, value in list(params.items()):
            if isinstance(value, str) and 'Bearer' in value:
                params[key] = sanitize_bearer_token(value)


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


@pytest.fixture
def creditor_service_provider_token_a() -> str:
    """
    Access token for Creditor Service Provider A.
    Used by tests that send or manage RTP as creditor.
    """
    return get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )


@pytest.fixture
def rtp_reader_access_token() -> str:
    """
    Access token for RTP Reader client.
    Used by tests that read RTP status.
    """
    return get_valid_access_token(
        client_id=secrets.rtp_reader.client_id,
        client_secret=secrets.rtp_reader.client_secret,
        access_token_function=get_access_token,
    )


@pytest.fixture
def pagopa_payee_registry_token() -> str:
    """
    Access token for pagoPA payees registry client.
    Used by tests that call the Payees Registry API.
    """
    return get_valid_access_token(
        client_id=secrets.pagopa_integration_payee_registry.client_id,
        client_secret=secrets.pagopa_integration_payee_registry.client_secret,
        access_token_function=get_access_token,
    )


@pytest.fixture
def pagopa_service_providers_registry_token() -> str:
    """
    Access token for pagoPA service providers registry client.
    Used by tests that call the Service Providers Registry API.
    """
    return get_valid_access_token(
        client_id=secrets.pagopa_integration_service_registry.client_id,
        client_secret=secrets.pagopa_integration_service_registry.client_secret,
        access_token_function=get_access_token,
    )

# ============================================================
#  Activation fixtures (create activation, cursor helpers)
# ============================================================

@pytest.fixture
def make_activation(
    debtor_service_provider_token_a: str,
) -> Callable[[], Tuple[str, str]]:
    """
    Factory fixture:
    creates a debtor activation and returns (activation_id, debtor_fc).
    """
    def _create() -> Tuple[str, str]:
        debtor_fc: str = fake_fc()
        res = activate(
            debtor_service_provider_token_a,
            debtor_fc,
            secrets.debtor_service_provider.service_provider_id,
        )

        assert res.status_code == 201, f"Activation failed: {res.status_code} {res.text}"
        activation_id = res.headers['Location'].rstrip('/').split('/')[-1]
        return activation_id, debtor_fc

    return _create


@pytest.fixture
def next_cursor() -> Callable[[str], Optional[str]]:
    """
    Helper used in activation listing tests to extract the next activation id
    (cursor) from API responses.
    """
    return extract_next_activation_id


@pytest.fixture
def random_fiscal_code() -> str:
    """Generate a random fiscal code for tests that need a fresh debtor."""
    return fake_fc()


@pytest.fixture
def activate_payer(
    debtor_service_provider_token_a: str,
) -> Callable[[str, bool], object]:
    """
    Factory fixture to activate a payer for RTP tests.

    Usage:
        activation_response = activate_payer(payer_id)
        # or:
        activation_id = activate_payer(payer_id, return_id=True)
    """
    def _activate(payer_id: str, return_id: bool = False) -> object:
        res = activate(
            debtor_service_provider_token_a,
            payer_id,
            secrets.debtor_service_provider.service_provider_id,
        )
        assert res.status_code == 201, f"Activation failed: {res.status_code} {res.text}"

        if not return_id: return res

        location = res.headers.get('Location', '').rstrip('/')
        activation_id: Optional[str] = location.split('/')[-1] if location else None
        return activation_id

    return _activate

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
def environment(request: SubRequest) -> Dict[str, object]:
    """
    Parametrized environment fixture.

    For each test run it yields:
    - name: logical name (UAT / DEV)
    - is_dev: bool flag (True for DEV)
    - create_function / get_function / delete_function / update_function:
      bound callables for Debt Position API, already configured for the env
    - subscription_key, organization_id: env-specific settings
    """

    env: Dict[str, object] = dict(request.param)

    is_dev = bool(env['is_dev'])

    def _create_function(
        subscription_key: str,
        organization_id: str,
        payload: Mapping[str, object],
        to_publish: bool,
    ) -> object:
        return create_debt_position(
            subscription_key,
            organization_id,
            payload,
            to_publish,
            is_dev,
        )

    def _get_function(
        subscription_key: str,
        organization_id: str,
        iupd: str,
    ) -> object:
        return get_debt_position(
            subscription_key,
            organization_id,
            iupd,
            is_dev,
        )

    def _delete_function(
        subscription_key: str,
        organization_id: str,
        iupd: str,
    ) -> object:
        return delete_debt_position(
            subscription_key,
            organization_id,
            iupd,
            is_dev,
        )

    def _update_function(
        subscription_key: str,
        organization_id: str,
        iupd: str,
        payload: Mapping[str, object],
        to_publish: bool = True,
    ) -> object:
        return update_debt_position(
            subscription_key,
            organization_id,
            iupd,
            payload,
            to_publish,
            is_dev,
        )

    subscription_key: str = (
        secrets.debt_positions_dev.subscription_key
        if is_dev
        else secrets.debt_positions.subscription_key
    )
    organization_id: str = (
        secrets.debt_positions_dev.organization_id
        if is_dev
        else secrets.debt_positions.organization_id
    )

    env.update(
        {
            'create_function': _create_function,
            'get_function': _get_function,
            'delete_function': _delete_function,
            'update_function': _update_function,
            'subscription_key': subscription_key,
            'organization_id': organization_id,
        }
    )

    return env


# ============================================================
#  GPD data setup fixtures (Debt Position preconditions)
# ============================================================

@pytest.fixture
def setup_data(environment: Dict[str, object]) -> Dict[str, object]:
    """
    Prepare base test data for GPD / debt position tests:
    - generates synthetic IUPD and IUV
    - exposes env-specific subscription key and organization id
    """

    debtor_fc: str = fake_fc()
    iupd: str = generate_iupd()
    iuv: str = generate_iuv()

    subscription_key = str(environment['subscription_key'])
    organization_id = str(environment['organization_id'])

    return {
        'debtor_fc': debtor_fc,
        'iupd': iupd,
        'iuv': iuv,
        'subscription_key': subscription_key,
        'organization_id': organization_id,
    }


@pytest.fixture
def gpd_test_data(setup_data: Dict[str, object], debtor_service_provider_token_a: str) -> SimpleNamespace:
    """
    Convenience wrapper over setup_data that exposes fields as attributes
    and ensures the debtor is activated before GPD tests.

    e.g. gpd_test_data.debtor_fc, gpd_test_data.iupd, …
    """
    debtor_fc = setup_data['debtor_fc']

    activation_response = activate(
        debtor_service_provider_token_a,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id,
    )

    assert activation_response.status_code == 201, \
        f"Failed to activate debtor for GPD test: {activation_response.status_code} {activation_response.text}"

    return SimpleNamespace(**setup_data)


# ============================================================
# Debtor Service Provider mock PFX certificate fixture
# ============================================================

@pytest.fixture
def debtor_sp_mock_cert_key() -> Tuple[str, str]:
    """
    Returns (cert_path, key_path) for the debtor service provider mock PFX.
    """
    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )
    return cert, key


# ============================================================
# Access token to access process GPD sender API
# ============================================================
@pytest.fixture
def sp_activations_read_all_token() -> str:
    """
    Access token for the RTP Activations Read All client.
    Admin-like role that can read activations across all Service Providers.
    """
    return get_valid_access_token(
        client_id=secrets.read_rtp_activations.client_id,
        client_secret=secrets.read_rtp_activations.client_secret,
        access_token_function=get_access_token,
    )


@pytest.fixture
def rtp_consumer_access_token() -> str:
    """
    Access token for RTP Consumer client.
    Used to send messages directly to the GPD sender service.
    """
    return get_valid_access_token(
        client_id=secrets.rtp_consumer.client_id,
        client_secret=secrets.rtp_consumer.client_secret,
        access_token_function=get_access_token,
    )
