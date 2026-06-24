import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_04b_compliant import (
    generate_callback_data_DS_04b_compliant,
    generate_non_compliant_callback_data_DS_04b,
)
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_04b")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("An RTP callback is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_04b_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_04b_compliant(
    rtp_consumer_access_token,
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
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_04b_compliant,
        original_msg_id,
        is_document=False,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 200, (
        f"Error from callback, expected 200 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_04b")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "non_ds_04b_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_04b_compliant(
    debtor_sp_mock_cert_key,
):

    callback_data = generate_callback_data_DS_04b_compliant(bic="MOCKSP01")

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 403, (
        f"Expecting error from callback, expected 403 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_04b")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-04b compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_04b_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_04b_compliant(
    debtor_sp_mock_cert_key,
):

    callback_data = generate_callback_data_DS_04b_compliant(bic="MOCKSP99")

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Expecting error from callback, expected 400 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_04b")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Failed callback for non compliant DS-04b payload")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_04b_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_compliant_payload_DS_04b_compliant(
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
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    get_response_pre_callback = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_pre_callback.status_code == 200
    body = get_response_pre_callback.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT before callback, got {body['status']}"

    callback_data = build_callback_with_original_msg_id(
        generate_non_compliant_callback_data_DS_04b,
        original_msg_id,
        is_document=False,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Error from callback, expected 400 got {callback_response.status_code}"
    )

    get_response_post_callback = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_post_callback.status_code == 200
    body = get_response_post_callback.json()
    assert body["status"] == "SENT", (
        f"RTP status should remain unchanged after non compliant callback, got {body['status']}"
    )
