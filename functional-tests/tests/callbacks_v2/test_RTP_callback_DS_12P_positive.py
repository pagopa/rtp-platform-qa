import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_rfc_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_12P_positive_v2 import (
    generate_callback_data_DS_12P_positive_compliant,
    generate_non_compliant_callback_data_DS_12P_positive,
)
from utils.dataset_gpd_message import generate_gpd_delete_message_payload, generate_gpd_message_payload


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_12P - Positive")
@allure.story("Service provider sends a v2 RFC callback with CNCL status")
@allure.title("A v2 RFC callback DS12P CNCL is successfully received and RTP status is CANCELLED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_12p_positive_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rfc_callback_DS_12P_positive_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    random_fiscal_code,
):
    """
    Test v2 RFC callback DS12P with CNCL status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message v2 (CREATE VALID)
    3. Cancel the RTP via GPD message v2 (DELETE) -> RTP to RFC_SENT
    4. Send DS12P callback with CxlStsId CNCL (Cancelled As Per Request)
    5. Verify callback is accepted (200)
    6. Verify RTP status is CANCELLED
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(
        access_token=rtp_consumer_access_token, message_payload=delete_payload
    )
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_positive_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 200, (
        f"Error from callback, expected 200 got {callback_response.status_code}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "CANCELLED", f"Expected status CANCELLED, got {body['status']}"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_12P - Positive")
@allure.story("Service provider sends a v2 RFC callback with CNCL status")
@allure.title("Unauthorized v2 RFC callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_12p_positive_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_wrong_certificate_serial_DS_12P_positive_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    random_fiscal_code,
):
    """
    Test v2 RFC callback DS12P with wrong certificate identity.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message v2 (CREATE VALID)
    3. Cancel the RTP via GPD message v2 (DELETE) -> RTP to RFC_SENT
    4. Send DS12P callback with assignee_bic='FAKESP01' (doesn't match certificate identity)
    5. Verify callback is rejected with 403 (certificate mismatch)
    6. Verify RTP status is still RFC_SENT
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(
        access_token=rtp_consumer_access_token, message_payload=delete_payload
    )
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_positive_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic="FAKESP01",
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 403, (
        f"Expecting error from callback, expected 403 got {callback_response.status_code}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "RFC_SENT", f"Expected status RFC_SENT, got {body['status']}"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_12P - Positive")
@allure.story("Service provider sends a v2 RFC callback with CNCL status")
@allure.title("Failed v2 RFC callback for non existing Service Provider - DS-12P positive compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_12p_positive_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_non_existing_service_provider_DS_12P_positive_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    random_fiscal_code,
):
    """
    Test v2 RFC callback DS12P with non-existing service provider.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message v2 (CREATE VALID)
    3. Cancel the RTP via GPD message v2 (DELETE) -> RTP to RFC_SENT
    4. Send DS12P callback with non-existing BIC (MOCKSP99)
    5. Verify callback is rejected with 400 (service provider not found)
    6. Verify RTP status is still RFC_SENT
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(
        access_token=rtp_consumer_access_token, message_payload=delete_payload
    )
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_positive_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic="MOCKSP99",
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Expecting error from callback, expected 400 got {callback_response.status_code}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "RFC_SENT", f"Expected status RFC_SENT, got {body['status']}"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_12P - Positive")
@allure.story("Service provider sends a v2 RFC callback with INVALID status")
@allure.title("A v2 RFC callback DS12P INVALID is rejected with 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_12p_invalid", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_rfc_callback_DS_12P_positive_invalid(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    random_fiscal_code,
):
    """
    Test v2 RFC callback DS12P with INVALID status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message v2 (CREATE VALID)
    3. Cancel the RTP via GPD message v2 (DELETE) -> RTP to RFC_SENT
    4. Send DS12P callback with CxlStsId INVALID
    5. Verify callback is rejected with 400
    6. Verify RTP status is still RFC_SENT
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(
        access_token=rtp_consumer_access_token, message_payload=delete_payload
    )
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_non_compliant_callback_data_DS_12P_positive(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Error from callback, expected 400 got {callback_response.status_code}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "RFC_SENT", f"Expected status RFC_SENT, got {body['status']}"