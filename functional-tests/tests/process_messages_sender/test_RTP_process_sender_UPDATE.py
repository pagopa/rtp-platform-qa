import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_delete_message_payload, generate_gpd_message_payload
from utils.response_assertions_utils import assert_body_presence, assert_response_code, get_response_body_safe
from utils.test_expectations import (
    UPDATE_AFTER_CREATE_AND_DELETE_CODES,
    UPDATE_EXPECTED_CODES,
    has_body_for_expected_code,
)


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender with different statuses")
@allure.title("An UPDATE message with status {status} after CREATE")
@allure.tag("functional", "gpd_message", "rtp_send", "update_parameterized")
@pytest.mark.send
@pytest.mark.parametrize("status", list(UPDATE_EXPECTED_CODES.keys()))
def test_send_gpd_message_update_scenarios(rtp_consumer_access_token, random_fiscal_code, activate_payer, status):
    """Test sending an UPDATE operation message with different statuses via GPD message API after a CREATE"""

    activate_payer(random_fiscal_code)

    create_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    response_create = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=create_payload)

    assert_response_code(response_create, 200, "CREATE", "VALID")

    iuv = create_payload["iuv"]
    msg_id = create_payload["id"]

    update_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="UPDATE", status=status, iuv=iuv, msg_id=msg_id
    )

    response_update = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=update_payload)

    expected_code = UPDATE_EXPECTED_CODES[status]
    assert_response_code(response_update, expected_code, "UPDATE", status)

    response_body = get_response_body_safe(response_update)
    assert_body_presence(response_body, has_body_for_expected_code(expected_code), "UPDATE", status)


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender with different statuses")
@allure.title("An UPDATE message with status {status} after CREATE VALID and DELETE")
@allure.tag("functional", "gpd_message", "rtp_send", "update_after_create_and_delete_parameterized")
@pytest.mark.send
@pytest.mark.parametrize("status", list(UPDATE_AFTER_CREATE_AND_DELETE_CODES.keys()))
def test_send_gpd_message_update_after_create_and_delete(
    rtp_consumer_access_token, random_fiscal_code, activate_payer, status
):
    """Test sending an UPDATE after CREATE VALID + DELETE with different statuses"""

    activate_payer(random_fiscal_code)

    create_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")
    assert_response_code(
        send_gpd_message(access_token=rtp_consumer_access_token, message_payload=create_payload), 200, "CREATE", "VALID"
    )

    iuv = create_payload["iuv"]
    msg_id = create_payload["id"]

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id, iuv=iuv)
    assert_response_code(
        send_gpd_message(access_token=rtp_consumer_access_token, message_payload=delete_payload), 200, "DELETE", "VALID"
    )

    update_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="UPDATE", status=status, iuv=iuv, msg_id=msg_id
    )
    response_update = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=update_payload)

    expected_code = UPDATE_AFTER_CREATE_AND_DELETE_CODES[status]
    assert_response_code(response_update, expected_code, "UPDATE after CREATE and DELETE", status)


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender with PAID status and invalid PSP tax code")
@allure.title("An UPDATE PAID message with an invalid PSP results in RFC_SENT state")
@allure.tag("functional", "unhappy_path", "gpd_message", "rtp_send", "update_paid")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_gpd_message_update_paid_unhappy_path(rtp_consumer_access_token, random_fiscal_code, activate_payer):
    """UPDATE PAID with psp_tax_code=None (invalid PSP) results in RTP state RFC_SENT"""

    activate_payer(random_fiscal_code)

    create_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")
    assert_response_code(
        send_gpd_message(access_token=rtp_consumer_access_token, message_payload=create_payload), 200, "CREATE", "VALID"
    )

    update_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation="UPDATE",
        status="PAID",
        iuv=create_payload["iuv"],
        msg_id=create_payload["id"],
        psp_tax_code=None,
    )
    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=update_payload)
    assert_response_code(response, 200, "UPDATE", "PAID")
    body = response.json()
    assert body["status"] == "RFC_SENT", f"Expected RTP state 'RFC_SENT', got '{body['status']}'"
