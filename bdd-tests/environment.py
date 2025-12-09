from typing import Dict

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets
from utils.dataset import fake_fc

from allure_commons._allure import dynamic


def _init_access_tokens() -> Dict[str, str]:
    """
    Align token management with what is done in functional tests
    (see functional-tests/tests/conftest.py).

    Returns a dict with:
    - debtor:    Debtor Service Provider A
    - debtor_b:  Debtor Service Provider B
    - creditor:  Creditor Service Provider A (if needed in RTP scenarios)
    """
    tokens: Dict[str, str] = {}

    tokens['debtor'] = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    tokens['debtor_b'] = get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token,
    )

    if getattr(secrets, 'creditor_service_provider', None):
        tokens['creditor'] = get_valid_access_token(
            client_id=secrets.creditor_service_provider.client_id,
            client_secret=secrets.creditor_service_provider.client_secret,
            access_token_function=get_access_token,
        )

    return tokens


def before_all(context) -> None:
    """
    Global Behave hook executed once at the start of the BDD suite.

    Initialize:
    - context.config
    - context.secrets
    - context.fake_fc
    - context.access_tokens
    """
    context.config = config
    context.secrets = secrets

    context.fake_fc = fake_fc

    context.access_tokens = _init_access_tokens()


def before_scenario(context, scenario) -> None:
    """
    Initializes/resets some holders used in steps to save state between
    Given/When/Then and labels BDD scenarios for Allure.
    """
    context.debtor_fc = {}

    context.latest_activation_response = None
    context.latest_rtp_response = None
    context.latest_rtp_resource_id = None

    context.otp = None

    dynamic.suite("BDD Scenarios")

    dynamic.label("test_type", "bdd")

    if scenario.feature and scenario.feature.name:
        dynamic.feature(scenario.feature.name)
