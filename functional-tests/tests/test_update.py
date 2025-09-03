"""
Functional tests for validating the update of debt positions
and their reflection in RTP (Request To Pay) lookups.

This suite:
- Creates a debt position with VALID status, optionally publishing it immediately.
- Updates the debt position and verifies changes are propagated correctly.
- Polls RTP lookup API until expected data is available or timeout is exceeded.

Pytest markers:
    - debt_positions: Marks tests related to debt positions.
    - happy_path: Marks tests that follow the expected success scenario.
    - timeout: Ensures tests fail if runtime exceeds configured timeout.

Allure integration provides feature and story annotations for reporting.
"""

import time
import allure
import pytest
from typing import NamedTuple, Any

from api.activation import activate
from api.auth import get_access_token, get_valid_access_token
from api.debt_position import create_debt_position, update_debt_position
from api.get_rtp import get_rtp_by_notice_number
from config.configuration import secrets, config
from utils.dataset import (
    create_debt_position_payload,
    create_debt_position_update_payload,
    fake_fc,
    generate_iupd,
    generate_iuv,
)


TEST_TIMEOUT_SEC = config.test_timeout_sec
POLLING_RATE_SEC = 30


class UpdateCheckData(NamedTuple):
    """
    Container for data needed to validate an update scenario.

    Attributes:
        nav (str): Notice number associated with the debt position.
        create_description (str): Description from the initial creation.
        create_amount (int): Amount from the initial creation.
        update_description (str): Description after the update.
        update_amount (int): Amount after the update.
    """
    nav: str
    create_description: str
    create_amount: int
    update_description: str
    update_amount: int


@pytest.fixture
def setup_data() -> dict[str, Any]:
    """
    Prepare data for debt position creation and activation.

    Returns:
        dict: A dictionary containing debtor fiscal code, identifiers, and
              configuration values needed to create debt positions.
    """
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    debtor_fc = fake_fc()

    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, "Error activating debtor before creating debt position"

    iupd = generate_iupd()
    iuv = generate_iuv()

    return {
        "debtor_fc": debtor_fc,
        "iupd": iupd,
        "iuv": iuv,
        "subscription_key": secrets.debt_positions.subscription_key,
        "organization_id": secrets.debt_positions.organization_id,
    }


@allure.feature("Debt Positions")
@allure.story("Update Valid Newly Published Debt Position")
@pytest.mark.debt_positions
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_update_valid_newly_published_debt_position(setup_data: dict[str, Any]) -> None:
    """
    Verify that a newly published debt position with VALID status
    can be updated and changes are reflected in RTP lookups.
    """
    allure.dynamic.title("Happy path: a newly published debt position with VALID status is updated")

    update_data = _setup_update_test(setup_data, "VALID", to_publish=False)
    access_token = _get_rtp_reader_access_token()
    expected_status = "SENT"

    while True:
        response = get_rtp_by_notice_number(access_token, update_data.nav)

        if response.status_code != 200:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {update_data.nav}"
            )

        data = response.json()
        assert isinstance(data, list), "Invalid response body."

        if len(data) == 0:
            time.sleep(POLLING_RATE_SEC)
            continue

        assert len(data) == 1

        rtp = data[0]
        assert rtp["status"] == expected_status, f"Wrong status. Expected {expected_status} but got {rtp['status']}"
        assert rtp["noticeNumber"] == update_data.nav
        assert rtp["description"] == update_data.update_description
        assert rtp["amount"] == update_data.update_amount
        assert update_data.update_description != update_data.create_description
        assert update_data.update_amount != update_data.create_amount

        break


@allure.feature("Debt Positions")
@allure.story("Update Valid Already Published Debt Position")
@pytest.mark.debt_positions
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_update_valid_already_published_debt_position(setup_data: dict[str, Any]) -> None:
    """
    Verify that an already published debt position with VALID status
    can be updated and changes are reflected in RTP lookups.
    """
    allure.dynamic.title("Happy path: an already published debt position with VALID status is updated")

    update_data = _setup_update_test(setup_data, "VALID")
    access_token = _get_rtp_reader_access_token()
    expected_status = "SENT"

    while True:
        response = get_rtp_by_notice_number(access_token, update_data.nav)

        if response.status_code != 200:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {update_data.nav}"
            )

        data = response.json()
        assert isinstance(data, list), "Invalid response body."

        if len(data) == 0:
            time.sleep(POLLING_RATE_SEC)
            continue

        assert len(data) == 2

        rtp_list = [rtp for rtp in data if rtp["status"] == expected_status]
        assert len(rtp_list) == 1, f"RTP list must contain exactly one item with status {expected_status}"

        rtp = rtp_list[0]
        assert rtp["status"] == expected_status
        assert rtp["noticeNumber"] == update_data.nav
        assert rtp["description"] == update_data.update_description
        assert rtp["amount"] == update_data.update_amount
        assert update_data.update_description != update_data.create_description
        assert update_data.update_amount != update_data.create_amount

        break


def _get_rtp_reader_access_token() -> str:
    """
    Retrieve a valid access token for the RTP reader client.

    Returns:
        str: A non-empty access token string.

    Raises:
        AssertionError: If no token is retrieved.
    """
    client_id = secrets.rtp_reader.client_id
    client_secret = secrets.rtp_reader.client_secret

    access_token = get_valid_access_token(
        client_id=client_id,
        client_secret=client_secret,
        access_token_function=get_access_token,
    )
    assert access_token is not None, "Access token cannot be None"
    return access_token


def _setup_update_test(
    setup_data: dict[str, Any],
    status: str,
    to_publish: bool = True,
    waiting_time_sec: int = 5,
) -> UpdateCheckData:
    """
    Create and update a debt position, returning both the original
    and updated values for validation.

    Args:
        setup_data (dict): Pre-computed setup data including identifiers and keys.
        status (str): Expected status of the created/updated debt position.
        to_publish (bool, optional): Whether to publish immediately. Defaults to True.
        waiting_time_sec (int, optional): Delay between creation/update and checks. Defaults to 5.

    Returns:
        UpdateCheckData: Structured data for validating the update.
    """
    subscription_key = setup_data["subscription_key"]
    organization_id = setup_data["organization_id"]
    debtor_fc = setup_data["debtor_fc"]
    iupd = setup_data["iupd"]
    iuv = setup_data["iuv"]

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    create_response = create_debt_position(subscription_key, organization_id, payload, to_publish=to_publish)
    assert create_response.status_code == 201

    create_response_body = create_response.json()
    expected_created_status = status if to_publish else "DRAFT"
    assert create_response_body["status"] == expected_created_status

    nav = create_response_body["paymentOption"][0]["nav"]
    assert nav is not None

    create_description = create_response_body["paymentOption"][0]["description"]
    create_amount = create_response_body["paymentOption"][0]["amount"]

    time.sleep(waiting_time_sec)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_debt_position(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200

    update_response_body = update_response.json()
    assert update_response_body["status"] == status

    time.sleep(waiting_time_sec)

    update_description = update_response_body["paymentOption"][0]["description"]
    update_amount = update_response_body["paymentOption"][0]["amount"]

    return UpdateCheckData(nav, create_description, create_amount, update_description, update_amount)
