from collections.abc import Callable, Generator, MutableMapping

import pytest
from _pytest.nodes import Item
from _pytest.reports import TestReport

from api.auth_api import get_keycloak_access_token, get_valid_access_token
from api.debtor_activation_api import activate
from config.configuration import config, secrets
from utils.cryptography_utils import pfx_to_pem
from utils.extract_next_activation_id import extract_next_activation_id
from utils.fiscal_code_utils import fake_fc
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

    if hasattr(item, "callspec") and hasattr(item.callspec, "params"):
        params: MutableMapping[str, object] = item.callspec.params
        for key, value in list(params.items()):
            if isinstance(value, str) and "Bearer" in value:
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
    )


# ============================================================
#  Keycloak access token fixtures
# ============================================================


@pytest.fixture
def kc_debtor_service_provider_token_a() -> str:
    """
    Keycloak access token for Debtor Service Provider A.
    """
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_debtor_service_provider_token_b() -> str:
    """
    Keycloak access token for Debtor Service Provider B.
    """
    return get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_creditor_service_provider_token_a() -> str:
    """
    Keycloak access token for Creditor Service Provider A.
    """
    return get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_rtp_reader_access_token() -> str:
    """
    Keycloak access token for RTP Reader client.
    """
    return get_valid_access_token(
        client_id=secrets.rtp_reader.client_id,
        client_secret=secrets.rtp_reader.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_pagopa_payee_registry_token() -> str:
    """
    Keycloak access token for pagoPA payees registry client.
    """
    return get_valid_access_token(
        client_id=secrets.pagopa_integration_payee_registry.client_id,
        client_secret=secrets.pagopa_integration_payee_registry.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_pagopa_service_providers_registry_token() -> str:
    """
    Keycloak access token for pagoPA service providers registry client.
    """
    return get_valid_access_token(
        client_id=secrets.pagopa_integration_service_registry.client_id,
        client_secret=secrets.pagopa_integration_service_registry.client_secret,
        access_token_function=get_keycloak_access_token,
    )


@pytest.fixture
def kc_sp_activations_read_all_token() -> str:
    """
    Keycloak access token for the RTP Activations Read All client.
    """
    return get_valid_access_token(
        client_id=secrets.read_rtp_activations.client_id,
        client_secret=secrets.read_rtp_activations.client_secret,
        access_token_function=get_keycloak_access_token,
    )


# ============================================================
#  Activation fixtures (create activation, cursor helpers)
# ============================================================


@pytest.fixture
def make_activation(
    debtor_service_provider_token_a: str,
) -> Callable[[], tuple[str, str]]:
    """
    Factory fixture:
    creates a debtor activation and returns (activation_id, debtor_fc).
    """

    def _create() -> tuple[str, str]:
        debtor_fc: str = fake_fc()
        res = activate(
            debtor_service_provider_token_a,
            debtor_fc,
            secrets.debtor_service_provider.service_provider_id,
        )

        assert res.status_code == 201, f"Activation failed: {res.status_code} {res.text}"
        activation_id = res.headers["Location"].rstrip("/").split("/")[-1]
        return activation_id, debtor_fc

    return _create


@pytest.fixture
def next_cursor() -> Callable[[str], str | None]:
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

        if not return_id:
            return res

        location = res.headers.get("Location", "").rstrip("/")
        activation_id: str | None = location.split("/")[-1] if location else None
        return activation_id

    return _activate


# ============================================================
# Debtor Service Provider mock PFX certificate fixture
# ============================================================


@pytest.fixture
def debtor_sp_mock_cert_key() -> tuple[str, str]:
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
        access_token_function=get_keycloak_access_token,
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
        access_token_function=get_keycloak_access_token,
    )
