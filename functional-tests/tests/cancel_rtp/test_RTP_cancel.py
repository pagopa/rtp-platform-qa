import uuid

import allure
import pytest

from api.RTP_cancel_api import cancel_rtp
from api.RTP_process_sender import send_gpd_message
from utils.constants_text_helper import CANCEL_REASON_MODT, CANCEL_REASON_PAID
from utils.dataset_gpd_message import generate_gpd_message_payload

_INVALID_CANCEL_REASON = "INVALID_REASON"


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
