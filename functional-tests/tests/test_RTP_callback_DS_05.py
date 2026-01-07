import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_05_ACTC_compliant import generate_callback_data_DS_05_ACTC_compliant
from utils.dataset_RTP_data import generate_rtp_data

@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_05')
@allure.story('Service provider sends a callback referred to an RTP with status ACTC')
@allure.title('An RTP callback with status ACTC is successfully received')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'ds_05_actc_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_05_ACTC_compliant(
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):

    rtp_data = generate_rtp_data()

    activation_response = activate_payer(rtp_data['payer']['payerId'])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]
    original_msg_id = resource_id.replace('-', '')

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
    )
    assert (
        callback_response.status_code == 200
    ), f"Error from callback, expected 200 got {callback_response.status_code}"

    get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body['status'] == 'ACCEPTED'
