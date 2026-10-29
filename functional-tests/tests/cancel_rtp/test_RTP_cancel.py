import uuid

import allure
import pytest

from api.RTP_cancel_api import cancel_rtp, cancel_rtp_v2
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from config.configuration import secrets
from utils.constants_text_helper import CANCEL_REASON_MODT, CANCEL_REASON_PAID
from utils.dataset_gpd_message import generate_gpd_message_payload

_INVALID_CANCEL_REASON = "INVALID_REASON"


def _assert_rtp_status(reader_token, resource_id, expected_status):
    response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert response.status_code == 200, f"Error retrieving RTP status: {response.status_code}. Body: {response.text}"

    actual_status = response.json()["status"]
    assert actual_status == expected_status, f"Expected RTP status {expected_status}, got {actual_status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP is successfully cancelled with reason PAID")
@allure.tag("functional", "happy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.happy_path
def test_cancel_rtp_with_reason_paid(
    rtp_consumer_access_token, activate_payer, random_fiscal_code, creditor_service_provider_token_a
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP is successfully cancelled with reason MODT")
@allure.tag("functional", "happy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.happy_path
def test_cancel_rtp_with_reason_modt(
    rtp_consumer_access_token, activate_payer, random_fiscal_code, creditor_service_provider_token_a
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_MODT)
    assert cancel_response.status_code == 204


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP cancellation fails if resource ID does not exist")
@allure.tag("functional", "unhappy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.unhappy_path
def test_cancel_rtp_with_nonexistent_resource_id(creditor_service_provider_token_a):
    access_token = creditor_service_provider_token_a
    fake_resource_id = str(uuid.uuid4())

    cancel_response = cancel_rtp(access_token, fake_resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 404, "Expected 404 Not Found for non-existent resource"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP cancellation fails with an invalid reason")
@allure.tag("functional", "unhappy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.unhappy_path
def test_cancel_rtp_with_invalid_reason(
    rtp_consumer_access_token, activate_payer, random_fiscal_code, creditor_service_provider_token_a
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, _INVALID_CANCEL_REASON)
    assert cancel_response.status_code == 400, "Expected 400 Bad Request for invalid cancel reason"


# ── V2 variants ──────────────────────────────────────────────────────────────
# These replicate the tests above using the v2 cancel endpoint
# (same URL /rtps/cancel but with Version: v2 header).


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP is successfully cancelled with reason {cancel_reason} - V2")
@allure.tag("functional", "happy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.happy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_cancel_rtp_with_reason_v2(
    rtp_consumer_access_token, activate_payer, random_fiscal_code, creditor_service_provider_token_a, cancel_reason
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"

    cancel_response = cancel_rtp_v2(creditor_service_provider_token_a, resource_id, cancel_reason)
    assert cancel_response.status_code == 204


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP cancellation fails if resource ID does not exist - V2")
@allure.tag("functional", "unhappy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.unhappy_path
def test_cancel_rtp_with_nonexistent_resource_id_v2(creditor_service_provider_token_a):
    access_token = creditor_service_provider_token_a
    fake_resource_id = str(uuid.uuid4())

    cancel_response = cancel_rtp_v2(access_token, fake_resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 404, "Expected 404 Not Found for non-existent resource"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP cancellation fails with an invalid reason - V2")
@allure.tag("functional", "unhappy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.unhappy_path
def test_cancel_rtp_with_invalid_reason_v2(
    rtp_consumer_access_token, activate_payer, random_fiscal_code, creditor_service_provider_token_a
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"

    cancel_response = cancel_rtp_v2(creditor_service_provider_token_a, resource_id, _INVALID_CANCEL_REASON)
    assert cancel_response.status_code == 400, "Expected 400 Bad Request for invalid cancel reason"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP using mock NAV scenarios")
@allure.title("RTP cancellation with CNCL mock NAV")
@allure.tag("functional", "rtp_cancel", "mock")
@pytest.mark.cancel
@pytest.mark.mock
def test_cancel_rtp_mock_cncl_cancel_nav(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    creditor_service_provider_token_a,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CREATE", status="VALID", nav=secrets.mock_cncl_cancel_nav
    )
    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204
    _assert_rtp_status(rtp_reader_access_token, resource_id, "CANCELLED_ACCR")


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP using mock NAV scenarios")
@allure.title("RTP cancellation with invalid mock NAV")
@allure.tag("functional", "rtp_cancel", "mock")
@pytest.mark.cancel
@pytest.mark.mock
def test_cancel_rtp_mock_invalid_nav(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    creditor_service_provider_token_a,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CREATE", status="VALID", nav=secrets.mock_invalid_nav
    )
    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204
    _assert_rtp_status(rtp_reader_access_token, resource_id, "RFC_SENT")


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP using mock NAV scenarios")
@allure.title("RTP cancellation with non-conformant mock response body")
@allure.tag("functional", "rtp_cancel", "mock")
@pytest.mark.cancel
@pytest.mark.mock
def test_cancel_rtp_mock_non_conformant_body_nav(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    creditor_service_provider_token_a,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation="CREATE",
        status="VALID",
        nav=secrets.mock_non_conformant_body_nav,
    )
    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204
    _assert_rtp_status(rtp_reader_access_token, resource_id, "RFC_SENT")


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP using mock NAV scenarios")
@allure.title("RTP cancellation with simple-string mock response")
@allure.tag("functional", "rtp_cancel", "mock")
@pytest.mark.cancel
@pytest.mark.mock
def test_cancel_rtp_mock_simple_string_nav(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    creditor_service_provider_token_a,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CREATE", status="VALID", nav=secrets.mock_simple_string_nav
    )
    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204
    _assert_rtp_status(rtp_reader_access_token, resource_id, "RFC_SENT")


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP using mock NAV scenarios")
@allure.title("RTP cancellation with unquoted-string mock response")
@allure.tag("functional", "rtp_cancel", "mock")
@pytest.mark.cancel
@pytest.mark.mock
def test_cancel_rtp_mock_string_no_quotes_nav(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    creditor_service_provider_token_a,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CREATE", status="VALID", nav=secrets.mock_string_no_quotes_nav
    )
    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204
    _assert_rtp_status(rtp_reader_access_token, resource_id, "RFC_SENT")
