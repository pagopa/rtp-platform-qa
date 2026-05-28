import allure
import pytest

from api.RTP_callback_api import srtp_rfc_callback
from api.RTP_cancel_api import cancel_rtp
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.constants_text_helper import CANCEL_REASON_MODT, CANCEL_REASON_PAID
from utils.dataset_callback_data_DS_12_invalid import generate_callback_data_DS_12_invalid
from utils.dataset_callback_data_DS_12N_RJCR_compliant import generate_callback_data_DS_12N_RJCR_compliant
from utils.dataset_gpd_message import generate_gpd_delete_message_payload, generate_gpd_message_payload


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("An RFC callback DS12N RJCR is successfully received and RTP status is ERROR_CANCEL")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rfc_callback_DS_12N_RJCR_compliant(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
):
    """
    Test RFC callback DS12N with RJCR status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (DELETE) → RTP to RFC_SENT
    4. Send DS12N callback with CxlStsId RJCR (Rejected Cancellation Request)
    5. Verify callback is accepted (200)
    6. Verify RTP status is ERROR_CANCEL
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
    assert body["status"] == "ERROR_CANCEL", f"Expected status ERROR_CANCEL, got {body['status']}"


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("Unauthorized RFC callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_wrong_certificate_serial_DS_12N_RJCR_compliant(
    rtp_consumer_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
):
    """
    Test RFC callback DS12N with wrong certificate identity.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (DELETE) → RTP to RFC_SENT
    4. Send DS12N callback with assignee_bic='MOCKSP01' (doesn't match certificate identity MOCKSP04)
    5. Verify callback is rejected with 403 (certificate mismatch)
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("Failed RFC callback for non existing Service Provider - DS-12N RJCR compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_non_existing_service_provider_DS_12N_RJCR_compliant(
    rtp_consumer_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
):
    """
    Test RFC callback DS12N with non-existing service provider.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (DELETE) → RTP to RFC_SENT
    4. Send DS12N callback with non-existing BIC (MOCKSP99)
    5. Verify callback is rejected with 400 (service provider not found)
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with INVALID status")
@allure.title("An RFC callback DS12N INVALID is rejected with 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_invalid", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_rfc_callback_DS_12N_invalid(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
):
    """
    Test RFC callback DS12N with INVALID status.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via GPD message (DELETE) → RTP to RFC_SENT
    4. Send DS12N callback with CxlStsId INVALID
    5. Verify callback is rejected with 400
    6. Verify RTP status is still RFC_SENT
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

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


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("An RFC callback DS12N RJCR is successfully received and RTP status is ERROR_CANCEL - through Web API cancel")
@allure.tag("functional", "happy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.happy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_receive_rfc_callback_DS_12N_RJCR_compliant_THROUGH_WEB_API(
    rtp_consumer_access_token,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12N with RJCR status, cancel triggered via REST Web API with explicit reason.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via REST cancel endpoint with cancel_reason → RTP to RFC_SENT
    4. Send DS12N callback with CxlStsId RJCR (Rejected Cancellation Request)
    5. Verify callback is accepted (200)
    6. Verify RTP status is ERROR_CANCEL
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, cancel_reason)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
    assert body["status"] == "ERROR_CANCEL", f"Expected status ERROR_CANCEL, got {body['status']}"


@allure.epic("RTP Callback")
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("Unauthorized RFC callback due to wrong certificate serial - through Web API cancel")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_fail_send_rfc_callback_wrong_certificate_serial_DS_12N_RJCR_compliant_THROUGH_WEB_API(
    rtp_consumer_access_token,
    creditor_service_provider_token_a,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12N with wrong certificate identity, cancel via REST Web API.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via REST cancel endpoint with cancel_reason → RTP to RFC_SENT
    4. Send DS12N callback with assignee_bic='MOCKSP01' (doesn't match certificate identity MOCKSP04)
    5. Verify callback is rejected with 403 (certificate mismatch)
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, cancel_reason)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with RJCR status")
@allure.title("Failed RFC callback for non existing Service Provider - DS-12N RJCR compliant - through Web API cancel")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_rjcr_compliant", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_fail_send_rfc_callback_non_existing_service_provider_DS_12N_RJCR_compliant_THROUGH_WEB_API(
    rtp_consumer_access_token,
    creditor_service_provider_token_a,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12N with non-existing service provider, cancel via REST Web API.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via REST cancel endpoint with cancel_reason → RTP to RFC_SENT
    4. Send DS12N callback with non-existing BIC (MOCKSP99)
    5. Verify callback is rejected with 400 (service provider not found)
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, cancel_reason)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
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
@allure.feature("RTP Callback DS_12N")
@allure.story("Service provider sends an RFC callback with INVALID status")
@allure.title("An RFC callback DS12N INVALID is rejected with 400 - through Web API cancel")
@allure.tag("functional", "unhappy_path", "rtp_callback", "ds_12n_invalid", "rfc")
@pytest.mark.callback
@pytest.mark.unhappy_path
@pytest.mark.parametrize("cancel_reason", [CANCEL_REASON_PAID, CANCEL_REASON_MODT])
def test_receive_rfc_callback_DS_12N_invalid_THROUGH_WEB_API(
    rtp_consumer_access_token,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
    activate_payer,
    random_fiscal_code,
    cancel_reason,
):
    """
    Test RFC callback DS12N with INVALID status, cancel via REST Web API.

    Flow:
    1. Activate payer
    2. Send an RTP via GPD message (CREATE VALID)
    3. Cancel the RTP via REST cancel endpoint with cancel_reason → RTP to RFC_SENT
    4. Send DS12N callback with CxlStsId INVALID
    5. Verify callback is rejected with 400
    6. Verify RTP status is still RFC_SENT
    """

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id, cancel_reason)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

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
