import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_callback_v2
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.callback_builder import build_callback_with_original_msg_id
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_callback_data_DS_document_rjct_v2 import generate_callback_data_DS_document_rjct_compliant
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP Callback V2")
@allure.feature("RTP Callback DS_document - Rejection")
@allure.story("Service provider sends a v2 document callback referred to an RTP with status RJCT")
@allure.title("A v2 document RTP callback with status RJCT is successfully received")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "ds_document_rjct_compliant")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_document_rjct_compliant(
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