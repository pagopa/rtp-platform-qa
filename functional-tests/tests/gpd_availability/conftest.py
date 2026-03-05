from collections.abc import Mapping
from types import SimpleNamespace

import pytest
from _pytest.fixtures import SubRequest

from api.debtor_activation_api import activate
from api.GPD_debt_position_api import (
    create_debt_position,
    delete_debt_position,
    get_debt_position,
    update_debt_position,
)
from config.configuration import secrets
from utils.fiscal_code_utils import fake_fc
from utils.generators_utils import generate_iupd, generate_iuv

# ============================================================
#  Environment fixture (UAT / DEV) + Debt Position helpers
# ============================================================


@pytest.fixture(
    params=[
        {"name": "UAT", "is_dev": False},
        {"name": "DEV", "is_dev": True},
    ],
    ids=["environment_uat", "environment_dev"],
)
def environment(request: SubRequest) -> dict[str, object]:
    """
    Parametrized environment fixture.

    For each test run it yields:
    - name: logical name (UAT / DEV)
    - is_dev: bool flag (True for DEV)
    - create_function / get_function / delete_function / update_function:
      bound callables for Debt Position API, already configured for the env
    - subscription_key, organization_id: env-specific settings
    """

    env: dict[str, object] = dict(request.param)

    is_dev = bool(env["is_dev"])

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
        secrets.debt_positions_dev.subscription_key if is_dev else secrets.debt_positions.subscription_key
    )
    organization_id: str = (
        secrets.debt_positions_dev.organization_id if is_dev else secrets.debt_positions.organization_id
    )

    env.update(
        {
            "create_function": _create_function,
            "get_function": _get_function,
            "delete_function": _delete_function,
            "update_function": _update_function,
            "subscription_key": subscription_key,
            "organization_id": organization_id,
        }
    )

    return env


# ============================================================
#  GPD data setup fixtures (Debt Position preconditions)
# ============================================================


@pytest.fixture
def setup_data(environment: dict[str, object]) -> dict[str, object]:
    """
    Prepare base test data for GPD / debt position tests:
    - generates synthetic IUPD and IUV
    - exposes env-specific subscription key and organization id
    """

    debtor_fc: str = fake_fc()
    iupd: str = generate_iupd()
    iuv: str = generate_iuv()

    subscription_key = str(environment["subscription_key"])
    organization_id = str(environment["organization_id"])

    return {
        "debtor_fc": debtor_fc,
        "iupd": iupd,
        "iuv": iuv,
        "subscription_key": subscription_key,
        "organization_id": organization_id,
    }


@pytest.fixture
def gpd_test_data(setup_data: dict[str, object], debtor_service_provider_token_a: str) -> SimpleNamespace:
    """
    Convenience wrapper over setup_data that exposes fields as attributes
    and ensures the debtor is activated before GPD tests.

    e.g. gpd_test_data.debtor_fc, gpd_test_data.iupd, …
    """
    debtor_fc = setup_data["debtor_fc"]

    activation_response = activate(
        debtor_service_provider_token_a,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id,
    )

    assert activation_response.status_code == 201, (
        f"Failed to activate debtor for GPD test: {activation_response.status_code} {activation_response.text}"
    )

    return SimpleNamespace(**setup_data)
