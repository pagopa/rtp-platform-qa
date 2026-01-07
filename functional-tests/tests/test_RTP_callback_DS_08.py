import allure
import pytest

from api.RTP_callback_api import srtp_callback
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp
from utils.callback_builder import build_callback_with_original_msg_id
from utils.dataset_callback_data_DS_05_ACTC_compliant import generate_callback_data_DS_05_ACTC_compliant
from utils.dataset_callback_data_DS_08N_compliant import generate_callback_data_DS_08N_compliant
from utils.dataset_callback_data_DS_08P_ACCP_compliant import generate_callback_data_DS_08P_ACCP_compliant
from utils.dataset_callback_data_DS_08P_ACWC_compliant import generate_callback_data_DS_08P_ACWC_compliant
from utils.dataset_callback_data_DS_08P_RJCT_compliant import generate_callback_data_DS_08P_RJCT_compliant
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received with status ACCP')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'DS_08P_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_compliant(
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

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_ACCP_compliant,
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
    assert body['status'] == 'USER_ACCEPTED'


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received with status ACCP')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'DS_08P_ACCP_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_compliant_ACCP(
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

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_ACCP_compliant,
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
    assert body['status'] == 'USER_ACCEPTED'


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received with status RJCT')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'ds_08p_RJCT_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_compliant_RJCT(
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

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_RJCT_compliant,
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
    assert body['status'] == 'USER_REJECTED'


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Failed callback for non existing Service Provider - DS-08P compliant')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_08n_compliant')
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


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP with status ACWC')
@allure.title('An RTP callback with status ACWC is successfully received')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'DS_08P_ACWC_compliant')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_rtp_callback_DS_08P_compliant_ACWC(
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

    initial_get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert initial_get_response.status_code == 200
    initial_body = initial_get_response.json()
    initial_status = initial_body['status']

    callback_data = build_callback_with_original_msg_id(
        generate_callback_data_DS_08P_ACWC_compliant,
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
        callback_response.status_code == 400
    ), f"Error from callback, expected 400 got {callback_response.status_code}"

    get_response = get_rtp(
        access_token=rtp_reader_access_token,
        rtp_id=resource_id,
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert (
        body['status'] == initial_status
    ), f"RTP status changed after ACWC callback: was {initial_status}, now {body['status']}"


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_08n_compliant')
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


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_08')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback with status REJECTED is successfully received')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'ds_08n_compliant')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08N_compliant(
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
