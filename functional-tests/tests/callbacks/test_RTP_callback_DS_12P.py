import allure
import pytest

from api.RTP_callback_api import srtp_rfc_callback
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.constants_text_helper import CANCEL_REASON_MODT, CANCEL_REASON_PAID
from utils.dataset_callback_data_DS_12_invalid import generate_callback_data_DS_12_invalid
from utils.dataset_callback_data_DS_12P_CNCL_compliant import generate_callback_data_DS_12P_CNCL_compliant
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12P")
@allure.story("Service provider sends an RFC callback with CNCL status")
@allure.title("An RFC callback DS12P CNCL is successfully received and RTP status is CANCEL")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_12p_cncl_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.happy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_receive_rfc_callback_DS_12P_CNCL_compliant(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12P with CNCL status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (CANCEL)
    4. Send DS12P callback with CxlStsId CNCL (Cancelled As Per Request)
    5. Verify callback is accepted (200)
    6. Verify RTP status is CANCELLED
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CANCEL", msg_id=message_payload["id"], iuv=message_payload["iuv"]
    )
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=cancel_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_CNCL_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
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
    assert body["status"] == "CANCELLED", f"Expected status CANCELLED, got {body['status']}"


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12P")
@allure.story("Service provider sends an RFC callback with CNCL status")
@allure.title("Unauthorized RFC callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12p_cncl_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_fail_send_rfc_callback_wrong_certificate_serial_DS_12P_CNCL_compliant(
    rtp_consumer_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12P with wrong certificate identity.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (CANCEL)
    4. Send DS12P callback with assignee_bic='MOCKSP01' which doesn't match the certificate's identity (MOCKSP04)
    5. Verify callback is rejected with 403 (certificate mismatch)

    Expected: 403 Forbidden - The server should reject the callback because the BIC in the
    Assgne field doesn't match the identity in the client certificate.
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CANCEL", msg_id=message_payload["id"], iuv=message_payload["iuv"]
    )
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=cancel_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_CNCL_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic="MOCKSP01",
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert callback_response.status_code == 403, (
        f"Expecting error from callback, expected 403 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12P")
@allure.story("Service provider sends an RFC callback with CNCL status")
@allure.title("Failed RFC callback for non existing Service Provider - DS-12P CNCL compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12p_cncl_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_fail_send_rfc_callback_non_existing_service_provider_DS_12P_CNCL_compliant(
    rtp_consumer_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12P with non-existing service provider.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (CANCEL)
    4. Send DS12P callback with non-existing BIC (MOCKSP99)
    5. Verify callback is rejected with 400 (service provider not found)

    Expected: 400 Bad Request
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CANCEL", msg_id=message_payload["id"], iuv=message_payload["iuv"]
    )
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=cancel_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12P_CNCL_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic="MOCKSP99",
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert callback_response.status_code == 400, (
        f"Expecting error from callback, expected 400 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12P")
@allure.story("Service provider sends an RFC callback with INVALID status")
@allure.title("An RFC callback DS12P INVALID is rejected with 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12p_invalid", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_receive_rfc_callback_DS_12P_invalid(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12P with INVALID status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (CANCEL)
    4. Send DS12P callback with CxlStsId INVALID (Invalid Cancellation Request)
    5. Verify callback is rejected with 400
    6. Verify RTP status is still RFC_SENT
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, f"Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code, operation="CANCEL", msg_id=message_payload["id"], iuv=message_payload["iuv"]
    )
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=cancel_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12_invalid(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
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
    assert body["status"] == "RFC_SENT", f"Expected status RFC_SENT, got {body['status']}"

