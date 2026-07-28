"""Regression tests: all v2 callback endpoints must reject requests that include the Version header.

The v2 callback endpoints are versioned via the URL path (``/v2/...``), so sending a
``Version`` header alongside the request is rejected with a 400 Bad Request.
Each test sends a syntactically valid v2 payload over mTLS WITH the ``Version`` header and
verifies the callback is rejected (400, with the expected error body) and the RTP state is
not affected.
If any of these tests begin returning 200 it means versioned routing via header has been
re-introduced - a regression.

Coverage:
- DS_05 redirect   (RTP callback v2 endpoint)
- DS_08P positive  (RTP callback v2 endpoint)
- DS_08N negative  (RTP callback v2 endpoint)
- DS_document RJCT (RTP callback v2 endpoint)
- DS_12P positive  (RFC callback v2 endpoint)
- DS_12N negative  (RFC callback v2 endpoint)
"""

import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_callback_v2, srtp_rfc_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.callback_builder import build_callback_with_original_msg_id
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_05_redirect_v2 import generate_callback_data_DS_05_redirect_compliant
from utils.dataset_callback_data_DS_08N_negative_v2 import generate_callback_data_DS_08N_negative_compliant
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.dataset_callback_data_DS_12N_negative_v2 import generate_callback_data_DS_12N_negative_compliant
from utils.dataset_callback_data_DS_12P_positive_v2 import generate_callback_data_DS_12P_positive_compliant
from utils.dataset_callback_data_DS_document_rjct_v2 import generate_callback_data_DS_document_rjct_compliant
from utils.dataset_gpd_message import generate_gpd_delete_message_payload, generate_gpd_message_payload

VERSION_HEADER_ERROR_MESSAGE = "Header 'Version' must not be sent for callback APIs."


def _assert_version_header_rejected(callback_response):
    assert callback_response.status_code == 400, (
        f"Expected 400 (Version header should be rejected) but got {callback_response.status_code}"
    )
    error_body = callback_response.json()
    assert error_body["status"] == 400
    assert error_body["error"] == "Bad Request"
    assert error_body["message"] == VERSION_HEADER_ERROR_MESSAGE


# ---------------------------------------------------------------------------
# RTP callback v2 endpoint (DS_05, DS_08P, DS_08N, DS_document)
# ---------------------------------------------------------------------------


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_05 redirect v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_05_redirect_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_redirect_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_08P positive v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_08P_positive_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_positive_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_08N negative v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_08N_negative_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

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
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_document RJCT v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_document_rjct_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_document_rjct_compliant,
        original_msg_id,
        is_document=False,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


# ---------------------------------------------------------------------------
# RFC callback v2 endpoint (DS_12P, DS_12N)
# ---------------------------------------------------------------------------


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_12P positive RFC v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "rfc", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rfc_callback_DS_12P_positive_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

    callback_data = generate_callback_data_DS_12P_positive_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback V2 - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_12N negative RFC v2 callback with Version header returns 400")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "rfc", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rfc_callback_DS_12N_negative_with_version_header(
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
    assert activation_response.status_code == 201

    send_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200, f"Error sending GPD message, expected 200 got {send_response.status_code}"

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    delete_payload = generate_gpd_delete_message_payload(msg_id=message_payload["id"], iuv=message_payload["iuv"])
    cancel_response = send_gpd_message_v2(access_token=rtp_consumer_access_token, message_payload=delete_payload)
    assert cancel_response.status_code == 200, f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"

    pre_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

    callback_data = generate_callback_data_DS_12N_negative_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback_v2(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    _assert_version_header_rejected(callback_response)

    post_callback_response = get_rtp_v2(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )
