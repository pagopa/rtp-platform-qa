import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.callback_builder import build_callback_with_original_msg_id
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_05_redirect_v2 import generate_callback_data_DS_05_redirect_compliant
from utils.dataset_callback_data_DS_08P_positive_v2 import (
    generate_callback_data_DS_08P_positive_compliant,
    generate_non_compliant_callback_data_DS_08P_positive,
)
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP with status ACCP")
@allure.title("A v2 RTP callback with status ACCP is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_positive_compliant(
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

    certificate, key = debtor_sp_mock_cert_key

    # Advance to ACCEPTED via DS_05 redirect ACTC
    ds05_callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_redirect_compliant,
        original_msg_id,
        is_document=True,
    )
    ds05_response = srtp_callback_v2(
        rtp_payload=ds05_callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert ds05_response.status_code == 200, (
        f"DS_05 setup step failed: expected 200 got {ds05_response.status_code}. Response: {ds05_response.text}"
    )

    get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200, (
        f"Expected 200, got {get_response.status_code}. Response: {get_response.text}"
    )
    assert get_response.json()["status"] == "ACCEPTED"

    # Now send DS_08P ACCP
    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_positive_compliant,
        original_msg_id,
        is_document=True,
    )

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
    assert body["status"] == "USER_ACCEPTED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP with status ACCP, skipping DS_05")
@allure.title("A v2 RTP callback with status ACCP is successfully received without a prior DS_05 callback")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_positive_compliant_without_DS_05(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """DS_08P ACCP callback sent directly on a SENT RTP (no prior DS_05 ACTC callback).

    The RTP is expected to transition straight from SENT to USER_ACCEPTED.
    """
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
    assert get_response_pre_callback.json()["status"] == "SENT", (
        f"Expected RTP status SENT before callback, got {get_response_pre_callback.json()['status']}"
    )

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_positive_compliant,
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
    assert body["status"] == "USER_ACCEPTED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_08P_positive_compliant(
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
        lambda: generate_callback_data_DS_08P_positive_compliant(bic="FAKESP01"),
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
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-08P positive compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_08P_positive_compliant(
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
        lambda: generate_callback_data_DS_08P_positive_compliant(bic="MOCKSP99"),
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
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP with invalid status")
@allure.title("A v2 RTP callback with invalid status is rejected without affecting the RTP status")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "non_ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_compliant_payload_DS_08P_positive(
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
        generate_non_compliant_callback_data_DS_08P_positive,
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


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_08P - Positive")
@allure.story("Service provider sends a v2 callback referred to an RTP with status ACCP")
@allure.title("Failed v2 callback for invalid RTP transition - DS-08P positive compliant")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "ds_08p_positive_compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_invalid_transition_DS_08P_positive_compliant(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """DS_08P ACCP callback sent twice on the same RTP (direct SENT -> USER_ACCEPTED).

    The second callback must be rejected with 400 since the transition is no
    longer valid once the RTP is already USER_ACCEPTED.
    """
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
        generate_callback_data_DS_08P_positive_compliant,
        original_msg_id,
        is_document=True,
    )

    certificate, key = debtor_sp_mock_cert_key

    first_callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert first_callback_response.status_code == 200, (
        f"Error from first callback, expected 200 got {first_callback_response.status_code}. "
        f"Response: {first_callback_response.text}"
    )

    first_get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert first_get_response.status_code == 200, (
        f"Expected 200, got {first_get_response.status_code}. Response: {first_get_response.text}"
    )
    body = first_get_response.json()
    assert body["status"] == "USER_ACCEPTED"

    second_callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
        include_version_header=False,
    )
    assert second_callback_response.status_code == 400, (
        f"Error from second callback, expected 400 got {second_callback_response.status_code}. "
        f"Response: {second_callback_response.text}"
    )

    second_get_response = get_rtp_v2(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert second_get_response.status_code == 200, (
        f"Expected 200, got {second_get_response.status_code}. Response: {second_get_response.text}"
    )
    body = second_get_response.json()
    assert body["status"] == "USER_ACCEPTED"
