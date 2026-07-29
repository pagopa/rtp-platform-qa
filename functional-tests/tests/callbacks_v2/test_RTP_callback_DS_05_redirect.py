import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.callback_builder import build_callback_with_original_msg_id
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_05_redirect_v2 import (
    generate_callback_data_DS_05_redirect_compliant,
    generate_non_compliant_callback_data_DS_05_redirect,
)
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_05 - Redirect")
@allure.story("Service provider sends a v2 redirect callback referred to an RTP with status ACTC")
@allure.title("A v2 redirect RTP callback with status ACTC is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_05_redirect_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_05_redirect_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201, (
        f"Expected 201, got {activation_response.status_code}. Response: {activation_response.text}"
    )

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, (
        f"Error sending GPD message, expected 200 got {send_response.status_code}. Response: {send_response.text}"
    )

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_redirect_compliant,
        original_msg_id,
        is_document=True,
    )

    certificate, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 200, (
        f"Error from callback, expected 200 got {callback_response.status_code}. Response: {callback_response.text}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200, (
        f"Expected 200, got {get_response.status_code}. Response: {get_response.text}"
    )
    body = get_response.json()
    assert body["status"] == "ACCEPTED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_05 - Redirect")
@allure.story("Service provider sends a v2 redirect callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_05_redirect_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_05_redirect_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201, (
        f"Expected 201, got {activation_response.status_code}. Response: {activation_response.text}"
    )

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, (
        f"Error sending GPD message, expected 200 got {send_response.status_code}. Response: {send_response.text}"
    )

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        lambda: generate_callback_data_DS_05_redirect_compliant(bic="FAKESP01"),
        original_msg_id,
        is_document=True,
    )

    certificate, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 403, (
        f"Expecting error from callback, expected 403 got {callback_response.status_code}. Response: {callback_response.text}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200, (
        f"Expected 200, got {get_response.status_code}. Response: {get_response.text}"
    )
    body = get_response.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT, got {body['status']}"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_05 - Redirect")
@allure.story("Service provider sends a v2 redirect callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-05 redirect compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_05_redirect_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_05_redirect_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201, (
        f"Expected 201, got {activation_response.status_code}. Response: {activation_response.text}"
    )

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, (
        f"Error sending GPD message, expected 200 got {send_response.status_code}. Response: {send_response.text}"
    )

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        lambda: generate_callback_data_DS_05_redirect_compliant(bic="MOCKSP99"),
        original_msg_id,
        is_document=True,
    )

    certificate, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Expecting error from callback, expected 400 got {callback_response.status_code}. Response: {callback_response.text}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200, (
        f"Expected 200, got {get_response.status_code}. Response: {get_response.text}"
    )
    body = get_response.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT, got {body['status']}"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_05 - Redirect")
@allure.story("Service provider sends a v2 redirect callback referred to an RTP with invalid status")
@allure.title("A v2 redirect RTP callback with invalid status is rejected without affecting the RTP status")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_05_redirect_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_compliant_payload_DS_05_redirect(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201, (
        f"Expected 201, got {activation_response.status_code}. Response: {activation_response.text}"
    )

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, (
        f"Error sending GPD message, expected 200 got {send_response.status_code}. Response: {send_response.text}"
    )

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    get_response_pre_callback = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_pre_callback.status_code == 200, (
        f"Expected 200, got {get_response_pre_callback.status_code}. Response: {get_response_pre_callback.text}"
    )
    body = get_response_pre_callback.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT before callback, got {body['status']}"

    callback_data = build_callback_with_original_msg_id(
        generate_non_compliant_callback_data_DS_05_redirect,
        original_msg_id,
        is_document=True,
    )

    certificate, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Error from callback, expected 400 got {callback_response.status_code}. Response: {callback_response.text}"
    )

    get_response_post_callback = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_post_callback.status_code == 200, (
        f"Expected 200, got {get_response_post_callback.status_code}. Response: {get_response_post_callback.text}"
    )
    body = get_response_post_callback.json()
    assert body["status"] == "SENT", (
        f"RTP status should remain unchanged after non compliant callback, got {body['status']}"
    )
