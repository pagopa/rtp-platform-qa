import uuid

import allure
import pytest

from api.RTP_cancel_api import cancel_rtp
from api.RTP_send_api import send_rtp
from utils.constants_text_helper import CANCEL_REASON_MODT, CANCEL_REASON_PAID
from utils.dataset_RTP_data import generate_rtp_data
from utils.http_utils import extract_id_from_location

_INVALID_CANCEL_REASON = "INVALID_REASON"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP is successfully cancelled with reason PAID")
@allure.tag("functional", "happy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.happy_path
def test_cancel_rtp_with_reason_paid(creditor_service_provider_token_a, activate_payer):
    rtp_data = generate_rtp_data()
    access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(access_token=access_token, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    resource_id = extract_id_from_location(send_response.headers.get("Location"))
    assert resource_id is not None, "Missing Location header in send RTP response"

    cancel_response = cancel_rtp(access_token, resource_id, CANCEL_REASON_PAID)
    assert cancel_response.status_code == 204


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP")
@allure.title("RTP is successfully cancelled with reason MODT")
@allure.tag("functional", "happy_path", "rtp_cancel")
@pytest.mark.cancel
@pytest.mark.happy_path
def test_cancel_rtp_with_reason_modt(creditor_service_provider_token_a, activate_payer):
    rtp_data = generate_rtp_data()
    access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(access_token=access_token, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    resource_id = extract_id_from_location(send_response.headers.get("Location"))
    assert resource_id is not None, "Missing Location header in send RTP response"

    cancel_response = cancel_rtp(access_token, resource_id, CANCEL_REASON_MODT)
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
def test_cancel_rtp_with_invalid_reason(creditor_service_provider_token_a, activate_payer):
    rtp_data = generate_rtp_data()
    access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(access_token=access_token, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    resource_id = extract_id_from_location(send_response.headers.get("Location"))
    assert resource_id is not None, "Missing Location header in send RTP response"

    cancel_response = cancel_rtp(access_token, resource_id, _INVALID_CANCEL_REASON)
    assert cancel_response.status_code == 400, "Expected 400 Bad Request for invalid cancel reason"
