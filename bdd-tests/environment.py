from typing import Dict

import allure

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets
from utils.dataset import fake_fc


def _init_access_tokens() -> Dict[str, str]:
    """
    Allinea la gestione dei token a quella dei functional tests.
    """
    tokens: Dict[str, str] = {}

    tokens["debtor"] = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    tokens["debtor_b"] = get_valid_access_token(
        client_id=secrets.debtor_service_provider_B.client_id,
        client_secret=secrets.debtor_service_provider_B.client_secret,
        access_token_function=get_access_token,
    )

    if getattr(secrets, "creditor_service_provider", None):
        tokens["creditor"] = get_valid_access_token(
            client_id=secrets.creditor_service_provider.client_id,
            client_secret=secrets.creditor_service_provider.client_secret,
            access_token_function=get_access_token,
        )

    return tokens


def before_all(context) -> None:
    context.config = config
    context.secrets = secrets
    context.fake_fc = fake_fc
    context.access_tokens = _init_access_tokens()


def before_scenario(context, scenario) -> None:
    context.debtor_fc = {}
    context.latest_activation_response = None
    context.latest_rtp_response = None
    context.latest_rtp_resource_id = None
    context.otp = None


    allure.label("parentSuite", "bdd-tests.tests")

    if scenario.feature and scenario.feature.name:
        allure.label("suite", scenario.feature.name)
        allure.feature(scenario.feature.name)
    else:
        allure.label("suite", "BDD Scenarios")

    allure.label("test_type", "bdd")
