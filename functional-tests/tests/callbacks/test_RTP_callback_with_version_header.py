"""Regression tests: all callback endpoints must reject requests that include the Version header.

The backend was updated to route callbacks without the ``Version`` header.  Sending the
header now causes the request to hit a removed/unknown route, returning 404.
Each test sends a syntactically valid payload over mTLS WITH the ``Version`` header and
verifies the callback is rejected (404) and the RTP state is not affected.
If any of these tests begin returning 200 it means versioned routing has been
re-introduced — a regression.

Coverage:
- DS_04b  (RTP callback endpoint)
- DS_05   (RTP callback endpoint)
- DS_08P  (RTP callback endpoint)
- DS_08N  (RTP callback endpoint)
- DS_12P  (RFC callback endpoint)
- DS_12N  (RFC callback endpoint)
"""

import allure
import pytest

from api.RTP_callback_api import srtp_callback, srtp_rfc_callback
from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_04b_compliant import generate_callback_data_DS_04b_compliant
from utils.dataset_callback_data_DS_05_ACTC_compliant import generate_callback_data_DS_05_ACTC_compliant
from utils.dataset_callback_data_DS_08N_compliant import generate_callback_data_DS_08N_compliant
from utils.dataset_callback_data_DS_08P_ACCP_compliant import generate_callback_data_DS_08P_ACCP_compliant
from utils.dataset_callback_data_DS_12N_RJCR_compliant import generate_callback_data_DS_12N_RJCR_compliant
from utils.dataset_callback_data_DS_12P_CNCL_compliant import generate_callback_data_DS_12P_CNCL_compliant
from utils.dataset_gpd_message import generate_gpd_delete_message_payload, generate_gpd_message_payload


# ---------------------------------------------------------------------------
# RTP callback endpoint (DS_04, DS_05, DS_08)
# ---------------------------------------------------------------------------


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_04b callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_04b_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_04b callback sent with the Version header must be rejected with 404.
    The RTP state must be unchanged.

    Flow:
    1. Activate payer and send an RTP → resource_id
    2. Capture current RTP status
    3. Build a valid DS_04b payload referencing the RTP
    4. POST to callback endpoint WITH Version header
    5. Verify 404 is returned
    6. Verify RTP status is unchanged
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    pre_callback_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert pre_callback_response.status_code == 200
    initial_status = pre_callback_response.json()["status"]

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
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    post_callback_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert post_callback_response.status_code == 200
    assert post_callback_response.json()["status"] == initial_status, (
        f"RTP status must be unchanged when Version header is present, got {post_callback_response.json()['status']}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_05 ACTC callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_05_ACTC_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_05 ACTC callback sent with the Version header must be rejected with 404.
    The RTP must remain in SENT (transition to ACCEPTED must not happen).

    Flow:
    1. Activate payer and send an RTP → resource_id
    2. Build a valid DS_05 ACTC payload referencing the RTP
    3. POST to callback endpoint WITH Version header
    4. Verify 404 is returned
    5. Verify RTP status is still SENT
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
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
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "SENT", (
        f"RTP status must remain SENT when Version header is present, got {body['status']}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_08P ACCP callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_08P_ACCP_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_08P ACCP callback sent with the Version header must be rejected with 404.
    The RTP must remain in ACCEPTED (transition to USER_ACCEPTED must not happen).

    Flow:
    1. Activate payer, send RTP, advance to ACCEPTED via DS_05 (without header)
    2. Build a valid DS_08P ACCP payload
    3. POST WITH Version header
    4. Verify 404 is returned
    5. Verify RTP status is still ACCEPTED
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    # Advance to ACCEPTED via DS_05 (without header)
    ds05_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_05_ACTC_compliant,
        original_msg_id,
        is_document=True,
    )
    cert, key = debtor_sp_mock_cert_key
    ds05_response = srtp_callback(
        rtp_payload=ds05_data,
        cert_path=cert,
        key_path=key,
        include_version_header=False,
    )
    assert ds05_response.status_code == 200, (
        f"DS_05 setup step failed: expected 200 got {ds05_response.status_code}"
    )

    # Now send DS_08P ACCP with Version header
    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_ACCP_compliant,
        original_msg_id,
        is_document=True,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "ACCEPTED", (
        f"RTP status must remain ACCEPTED when Version header is present, got {body['status']}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_08N callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rtp_callback_DS_08N_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_08N callback sent with the Version header must be rejected with 404.
    The RTP must remain in SENT (transition to REJECTED must not happen).

    Flow:
    1. Activate payer and send an RTP → resource_id
    2. Build a valid DS_08N payload referencing the RTP
    3. POST to callback endpoint WITH Version header
    4. Verify 404 is returned
    5. Verify RTP status is still SENT
    """
    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert resource_id is not None, "Missing resourceId in send GPD message response"
    original_msg_id = resource_id.replace("-", "")

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08N_compliant,
        original_msg_id,
        is_document=True,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "SENT", (
        f"RTP status must remain SENT when Version header is present, got {body['status']}"
    )


# ---------------------------------------------------------------------------
# RFC callback endpoint (DS_12P, DS_12N)
# ---------------------------------------------------------------------------


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_12P CNCL RFC callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "rfc", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rfc_callback_DS_12P_CNCL_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_12P CNCL RFC callback sent with the Version header must be rejected with 404.
    The RTP must remain in RFC_SENT (transition to CANCELLED must not happen).

    Flow:
    1. Activate payer, send RTP, trigger cancel via GPD DELETE → RFC_SENT
    2. Build a valid DS_12P CNCL payload
    3. POST to RFC callback endpoint WITH Version header
    4. Verify 404 is returned
    5. Verify RTP status is still RFC_SENT
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
    assert cancel_response.status_code == 200, (
        f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"
    )

    callback_data = generate_callback_data_DS_12P_CNCL_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "RFC_SENT", (
        f"RTP status must remain RFC_SENT when Version header is present, got {body['status']}"
    )


@allure.epic("RTP Callback")
@allure.feature("RTP Callback - Version Header")
@allure.story("Callback with Version header is rejected")
@allure.title("DS_12N RJCR RFC callback with Version header returns 404")
@allure.tag("functional", "unhappy_path", "rtp_callback", "rfc", "regression", "version_header")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_rfc_callback_DS_12N_RJCR_with_version_header(
    rtp_consumer_access_token,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
):
    """
    DS_12N RJCR RFC callback sent with the Version header must be rejected with 404.
    The RTP must remain in RFC_SENT (transition to ERROR_CANCEL must not happen).

    Flow:
    1. Activate payer, send RTP, trigger cancel via GPD DELETE → RFC_SENT
    2. Build a valid DS_12N RJCR payload
    3. POST to RFC callback endpoint WITH Version header
    4. Verify 404 is returned
    5. Verify RTP status is still RFC_SENT
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
    assert cancel_response.status_code == 200, (
        f"Error cancelling RTP via DELETE, got {cancel_response.status_code}"
    )

    callback_data = generate_callback_data_DS_12N_RJCR_compliant(
        resource_id=resource_id,
        original_msg_id=original_msg_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
        include_version_header=True,
    )
    assert callback_response.status_code == 404, (
        f"Expected 404 (Version header should be rejected) but got {callback_response.status_code}"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "RFC_SENT", (
        f"RTP status must remain RFC_SENT when Version header is present, got {body['status']}"
    )
