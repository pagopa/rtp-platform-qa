import allure
import pytest

from api.callback import srtp_callback
from api.get_rtp import get_rtp
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset import generate_callback_data_DS_04b_compliant
from utils.dataset import generate_callback_data_DS_05_ACTC_compliant
from utils.dataset import generate_callback_data_DS_08N_compliant
from utils.dataset import generate_rtp_data
from utils.callback_builder import build_callback_with_original_msg_id

@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_04b_compliant(
    creditor_service_provider_token_a,
    activate_payer,
    debtor_sp_mock_cert_key,
):

    rtp_data = generate_rtp_data()

    creditor_service_provider_access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data['payer']['payerId'])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token,
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


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08N_compliant(
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):
    rtp_data = generate_rtp_data()

    creditor_service_provider_access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data['payer']['payerId'])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token,
        rtp_payload=rtp_data,
    )

    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]
    original_msg_id = resource_id.replace('-', '')

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
    assert body['status'] == 'REJECTED'


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP with status ACTC')
@allure.title('An RTP callback with status ACTC is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_05_ACTC_compliant(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    debtor_sp_mock_cert_key,
):
    rtp_data = generate_rtp_data()

    creditor_service_provider_access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data['payer']['payerId'])
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token,
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


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
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


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_08N_compliant(
    debtor_sp_mock_cert_key,
):
    callback_data = generate_callback_data_DS_08N_compliant(BIC='MOCKSP01')

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 403
    ), f"Expecting error from callback, expected 403 got {callback_response.status_code}"


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Failed callback for non existing Service Provider - DS-04b compliant')
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


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Failed callback for non existing Service Provider - DS-08P compliant')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_08N_compliant(
    debtor_sp_mock_cert_key,
):
    callback_data = generate_callback_data_DS_08N_compliant(BIC='MOCKSP99')

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 400
    ), f"Expecting error from callback, expected 400 got {callback_response.status_code}"
