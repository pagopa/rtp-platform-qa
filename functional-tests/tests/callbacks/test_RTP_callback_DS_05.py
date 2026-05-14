import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_05_ACTC_compliant import (
    generate_callback_data_DS_05_ACTC_compliant,
    generate_invalid_callback_data_DS_05_ACTC,
)
from utils.dataset_RTP_data import generate_rtp_data
from utils.http_utils import extract_id_from_location


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_05")
@allure.story("Service provider sends a callback referred to an RTP with status ACTC")
@allure.title("An RTP callback with status ACTC is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_05_actc_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_05_ACTC_compliant(
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):

    rtp_data = generate_rtp_data()

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = extract_id_from_location(location)
    assert resource_id, f"Could not extract resource ID from Location header: {location}"
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
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):

    rtp_data = generate_rtp_data()

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = extract_id_from_location(location)
    assert resource_id, f"Could not extract resource ID from Location header: {location}"
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
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):

    rtp_data = generate_rtp_data()

    activation_response = activate_payer(rtp_data["payer"]["payerId"])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = extract_id_from_location(location)
    assert resource_id, f"Could not extract resource ID from Location header: {location}"
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
