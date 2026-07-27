import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.callback_builder import build_callback_with_original_msg_id
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_05_redirect_v2 import generate_callback_data_DS_05_redirect_compliant
from utils.dataset_callback_data_DS_08N_negative_v2 import (
    generate_callback_data_DS_08N_negative_compliant,
    generate_non_compliant_callback_data_DS_08N_negative,
)
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08N - Negative")
@allure.story("Service provider sends a v2 callback referred to an RTP with status RJCT")
@allure.title("A v2 RTP callback with status RJCT is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_08n_negative_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08N_negative_compliant(
    creditor_service_provider_token_a,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """DS_08N RJCT callback sent directly on a SENT RTP (no prior DS_05 ACTC callback).

    The RTP is expected to transition from SENT to REJECTED.
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=creditor_service_provider_token_a, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    get_response_pre_callback = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_pre_callback.status_code == 200
    assert get_response_pre_callback.json()["status"] == "SENT", (
        f"Expected RTP status SENT before callback, got {get_response_pre_callback.json()['status']}"
    )

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08N_negative_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
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
    assert body["status"] == "REJECTED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08N - Negative")
@allure.story("Service provider sends a v2 callback referred to an RTP with status RJCT, after DS_05")
@allure.title("A v2 RTP callback with status RJCT after DS_05 transitions the RTP to USER_REJECTED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_08n_negative_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08N_negative_compliant_after_DS_05(
    creditor_service_provider_token_a,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """DS_08N RJCT callback sent after a prior DS_05 ACTC callback.

    The RTP is expected to transition from SENT to ACCEPTED, then to USER_REJECTED.
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=creditor_service_provider_token_a, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    cert, key = debtor_sp_mock_cert_key

    # Advance to ACCEPTED via DS_05 redirect ACTC
    ds05_callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_redirect_compliant,
        original_msg_id,
        is_document=True,
    )
    ds05_response = srtp_callback_v2(
        rtp_payload=ds05_callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert ds05_response.status_code == 200, (
        f"DS_05 setup step failed: expected 200 got {ds05_response.status_code}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ACCEPTED"

    # Now send DS_08N RJCT
    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08N_negative_compliant,
        original_msg_id,
        is_document=True,
    )

    callback_response = srtp_callback_v2(
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
    assert body["status"] == "USER_REJECTED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08N - Negative")
@allure.story("Service provider sends a v2 callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_08n_negative_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_08N_negative_compliant(
    debtor_sp_mock_cert_key,
):
    callback_data = generate_callback_data_DS_08N_negative_compliant(bic="MOCKSP01")

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 403, (
        f"Expecting error from callback, expected 403 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08N - Negative")
@allure.story("Service provider sends a v2 callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-08N negative compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_08n_negative_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_08N_negative_compliant(
    debtor_sp_mock_cert_key,
):
    callback_data = generate_callback_data_DS_08N_negative_compliant(bic="MOCKSP99")

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Expecting error from callback, expected 400 got {callback_response.status_code}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08N - Negative")
@allure.story("Service provider sends a v2 callback referred to an RTP with invalid status")
@allure.title("A v2 RTP callback with invalid status is rejected without affecting the RTP status")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_08n_negative_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_compliant_payload_DS_08N_negative(
    creditor_service_provider_token_a,
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=creditor_service_provider_token_a, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    get_response_pre_callback = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_pre_callback.status_code == 200
    body = get_response_pre_callback.json()
    assert body["status"] == "SENT", f"Expected RTP status SENT before callback, got {body['status']}"

    callback_data = build_callback_with_original_msg_id(
        generate_non_compliant_callback_data_DS_08N_negative,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert callback_response.status_code == 400, (
        f"Error from callback, expected 400 got {callback_response.status_code}"
    )

    get_response_post_callback = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response_post_callback.status_code == 200
    body = get_response_post_callback.json()
    assert body["status"] == "SENT", (
        f"RTP status should remain unchanged after non compliant callback, got {body['status']}"
    )