import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_callback_api import srtp_rfc_callback
from api.RTP_cancel_api import cancel_rtp
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp
from config.configuration import secrets
from utils.callback_builder import build_rfc_callback_with_original_msg_id
from utils.dataset_callback_data_DS_12P_CNCL_compliant import generate_callback_data_DS_12P_CNCL_compliant
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_12P')
@allure.story('Service provider sends an RFC callback with CNCL status')
@allure.title('An RFC callback DS12P CNCL is successfully received and RTP status is CANCEL')
@allure.tag('functional', 'happy_path', 'rtp_callback', 'ds_12p_cncl_compliant', 'rfc')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rfc_callback_DS_12P_CNCL_compliant(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
):
    """
    Test RFC callback DS12P with CNCL status.

    Flow:
    1. Get debtor service provider token
    2. Activate payer to get fiscal code
    3. Get creditor service provider token
    4. Send an RTP
    5. Cancel the RTP (RFC - Request for Cancellation)
    6. Send DS12P callback with CxlStsId CNCL (Cancelled As Per Request)
    7. Verify callback is accepted (200)
    8. Verify RTP status is CANCEL
    """

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data['payer']['payerId'],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]
    original_msg_id = resource_id.replace('-', '')

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = build_rfc_callback_with_original_msg_id(
        generate_callback_data_DS_12P_CNCL_compliant,
        original_msg_id,
        resource_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
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
    assert body['status'] == 'CANCELLED', f"Expected status CANCELLED, got {body['status']}"


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_12P')
@allure.story('Service provider sends an RFC callback with CNCL status')
@allure.title('Unauthorized RFC callback due to wrong certificate serial')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_12p_cncl_compliant', 'rfc')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_wrong_certificate_serial_DS_12P_CNCL_compliant(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    debtor_sp_mock_cert_key,
):
    """
    Test RFC callback DS12P with wrong certificate identity.

    Flow:
    1. Get debtor service provider token
    2. Activate payer to get fiscal code
    3. Get creditor service provider token
    4. Send an RTP
    5. Cancel the RTP (RFC - Request for Cancellation)
    6. Send DS12P callback with assignee_bic='MOCKSP01' which doesn't match the certificate's identity (MOCKSP04)
    7. Verify callback is rejected with 403 (certificate mismatch)

    Expected: 403 Forbidden - The server should reject the callback because the BIC in the 
    Assgne field doesn't match the identity in the client certificate.
    """

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data['payer']['payerId'],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]
    original_msg_id = resource_id.replace('-', '')

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = build_rfc_callback_with_original_msg_id(
        lambda resource_id=None, original_msg_id=None: generate_callback_data_DS_12P_CNCL_compliant(
            resource_id=resource_id, original_msg_id=original_msg_id, assignee_bic='MOCKSP01'
        ),
        original_msg_id,
        resource_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 403
    ), f"Expecting error from callback, expected 403 got {callback_response.status_code}"


@allure.epic('RTP Callback')
@allure.feature('RTP Callback DS_12P')
@allure.story('Service provider sends an RFC callback with CNCL status')
@allure.title('Failed RFC callback for non existing Service Provider - DS-12P CNCL compliant')
@allure.tag('functional', 'unhappy_path', 'rtp_callback', 'ds_12p_cncl_compliant', 'rfc')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rfc_callback_non_existing_service_provider_DS_12P_CNCL_compliant(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    debtor_sp_mock_cert_key,
):
    """
    Test RFC callback DS12P with non-existing service provider.

    Flow:
    1. Get debtor service provider token
    2. Activate payer to get fiscal code
    3. Get creditor service provider token
    4. Send an RTP
    5. Cancel the RTP (RFC - Request for Cancellation)
    6. Send DS12P callback with non-existing BIC (MOCKSP99)
    7. Verify callback is rejected with 400 (service provider not found)

    Expected: 400 Bad Request
    """

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data['payer']['payerId'],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]
    original_msg_id = resource_id.replace('-', '')

    cancel_response = cancel_rtp(creditor_service_provider_token_a, resource_id)
    assert cancel_response.status_code == 204, f"Error cancelling RTP, got {cancel_response.status_code}"

    callback_data = build_rfc_callback_with_original_msg_id(
        lambda resource_id=None, original_msg_id=None: generate_callback_data_DS_12P_CNCL_compliant(
            resource_id=resource_id, original_msg_id=original_msg_id, assignee_bic='MOCKSP99'
        ),
        original_msg_id,
        resource_id,
    )

    cert, key = debtor_sp_mock_cert_key

    callback_response = srtp_rfc_callback(
        rtp_payload=callback_data,
        cert_path=cert,
        key_path=key,
    )
    assert (
        callback_response.status_code == 400
    ), f"Expecting error from callback, expected 400 got {callback_response.status_code}"
