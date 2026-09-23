import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_status_update_callback
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.dataset_status_update_callback import generate_status_update_callback_data


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider transitions an RTP through a status update callback")
@allure.title("A status update callback with reason code {reason_code} transitions SENT to {expected_status}")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
@pytest.mark.parametrize(
    ("reason_code", "expected_status"),
    [
        ("ALAC", "USER_ACCEPTED"),
        ("ARFR", "USER_REJECTED"),
        ("ARJR", "REJECTED"),
        ("AEXR", "EXPIRED"),
        ("IRNR", "ERROR_SEND"),
    ],
)
def test_receive_status_update_callback_sent_transitions(
    rtp_consumer_access_token,
    debtor_service_provider_token_c,
    rtp_reader_access_token,
    random_fiscal_code,
    debtor_sp_mock_cert_key,
    reason_code,
    expected_status,
):
    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation="CREATE",
        status="VALID",
    )

    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code == 201, (
        f"Expected 201, got {activation_response.status_code}. Response: {activation_response.text}"
    )

    send_response = send_gpd_message_v2(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload,
    )
    assert send_response.status_code == 200, (
        f"Error sending GPD message, expected 200 got {send_response.status_code}. Response: {send_response.text}"
    )

    resource_id = send_response.json()["resourceId"]
    assert resource_id, "Missing resourceId in send GPD message response"

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

    callback_data = generate_status_update_callback_data(
        bic=DEBTOR_SERVICE_PROVIDER_C_ID,
        resource_id=resource_id,
        original_msg_id=resource_id,
        reason_code=reason_code,
    )

    certificate, key = debtor_sp_mock_cert_key
    callback_response = srtp_status_update_callback(
        rtp_payload=callback_data,
        cert_path=certificate,
        key_path=key,
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
    assert get_response.json()["status"] == expected_status
