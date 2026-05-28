import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_05_ACTC_compliant import (
    generate_callback_data_DS_05_ACTC_compliant,
    generate_invalid_callback_data_DS_05_ACTC,
)
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_05")
@allure.story("Service provider sends a callback referred to an RTP with status ACTC")
@allure.title("An RTP callback with status ACTC is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_05_actc_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_05_ACTC_compliant(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_ACTC_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert callback_response.status_code == 200, (
        f"Error from callback, expected 200 got {callback_response.status_code}"
    )

    get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "ACCEPTED"


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_05")
@allure.story("Service provider sends a callback referred to an RTP with invalid status")
@allure.title(
    "An RTP callback with invalid status is received and processed with success without affecting the RTP status"
)
@allure.tag("functional", "unhappy_path", "rtp_callback", "non_ds_05_actc_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_rtp_callback_DS_05_ACTC_non_compliant(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    get_response_pre_callback = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_pre_callback.status_code == 200
    body = get_response_pre_callback.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT before callback, got {body['status']}"

    callback_data = build_callback_with_original_msg_id(
        generate_invalid_callback_data_DS_05_ACTC,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert callback_response.status_code == 400, (
        f"Error from callback, expected 400 got {callback_response.status_code}"
    )

    get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT after non-compliant callback, got {body['status']}"


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_05")
@allure.story("Service provider sends a callback referred to an RTP with status ACTC")
@allure.title("Failed callback for invalid RTP transition - DS-05 ACTC compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_05_actc_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_invalid_transition_DS_05_ACTC_compliant(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_ACTC_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    first_callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert first_callback_response.status_code == 200, (
        f"Error from first callback, expected 200 got {first_callback_response.status_code}"
    )

    first_get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert first_get_response.status_code == 200
    body = first_get_response.json()
    assert body["status"] == "ACCEPTED"

    second_callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert second_callback_response.status_code == 400, (
        f"Error from second callback, expected 400 got {second_callback_response.status_code}"
    )

    second_get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert second_get_response.status_code == 200
    body = second_get_response.json()
    assert body["status"] == "ACCEPTED"
