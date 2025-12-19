import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_send_api import send_rtp
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_04b_compliant import generate_callback_data_DS_04b_compliant
from utils.dataset_RTP_data import generate_rtp_data

@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_04b')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'ds_04b_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_04b_compliant(
    creditor_service_provider_token_a,
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
        generate_callback_data_DS_04b_compliant,
        original_msg_id,
        is_document=False,
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


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_04b')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_04b_compliant')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_04b_compliant(
    debtor_sp_mock_cert_key,
):

    callback_data = generate_callback_data_DS_04b_compliant(BIC='MOCKSP01')

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 403
    ), f"Expecting error from callback, expected 403 got {callback_response.status_code}"



@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_04b')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Failed callback for non existing Service Provider - DS-04b compliant')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_04b_compliant')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_04b_compliant(
    debtor_sp_mock_cert_key,
):

    callback_data = generate_callback_data_DS_04b_compliant(BIC='MOCKSP99')

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 400
    ), f"Expecting error from callback, expected 400 got {callback_response.status_code}"
