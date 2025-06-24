import allure
import pytest

from api.activation import activate
from api.auth import get_access_token, get_valid_access_token
from api.send_rtp import send_rtp
from utils.dataset import generate_rtp_data
from api.callback import srtp_callback
from config.configuration import config
from config.configuration import secrets
from utils.cryptography import pfx_to_pem
from utils.dataset import generate_callback_data_DS_04b_compliant
from utils.dataset import generate_callback_data_DS_08P_compliant


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("An RTP callback is successfully received")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_04b_compliant():

    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    activation_response = activate(
        debtor_service_provider_access_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = location.split("/")[-1]

    original_msg_id = resource_id.replace("-", "")

    callback_data = generate_callback_data_DS_04b_compliant()
    callback_data["AsynchronousSepaRequestToPayResponse"]["CdtrPmtActvtnReqStsRpt"][
        "OrgnlGrpInfAndSts"
    ]["OrgnlMsgId"] = original_msg_id

    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 200
    ), f"Error from callback, expected 200 got {callback_response.status_code}"


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("An RTP callback is successfully received")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_compliant():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    activation_response = activate(
        debtor_service_provider_access_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = location.split("/")[-1]

    original_msg_id = resource_id.replace("-", "")

    callback_data = generate_callback_data_DS_08P_compliant()
    callback_data["AsynchronousSepaRequestToPayResponse"]["Document"]["CdtrPmtActvtnReqStsRpt"][
        "OrgnlGrpInfAndSts"
    ]["OrgnlMsgId"] = original_msg_id

    print('callback_data', callback_data)
    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 200
    ), f"Error from callback, expected 200 got {callback_response.status_code}"


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_04b_compliant():
    callback_data = generate_callback_data_DS_04b_compliant(BIC="MOCKSP01")

    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 403
    ), f"Expecting error from callback, expected 403 got {callback_response.status_code}"


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Unauthorized callback due to wrong certificate serial")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_08P_compliant():
    callback_data = generate_callback_data_DS_08P_compliant(BIC="MOCKSP01")

    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 403
    ), f"Expecting error from callback, expected 403 got {callback_response.status_code}"


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-04b compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_04b_compliant():
    callback_data = generate_callback_data_DS_04b_compliant(BIC="MOCKSP99")

    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 400
    ), f"Expecting error from callback, expected 400 got {callback_response.status_code}"


@allure.feature("RTP Callback")
@allure.story("Service provider sends a callback referred to an RTP")
@allure.title("Failed callback for non existing Service Provider - DS-08P compliant")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_non_existing_service_provider_DS_08P_compliant():
    callback_data = generate_callback_data_DS_08P_compliant(BIC="MOCKSP99")

    cert, key = pfx_to_pem(
        secrets.debtor_service_provider_mock_PFX_base64,
        secrets.debtor_service_provider_mock_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )

    callback_response = srtp_callback(
        rtp_payload=callback_data, cert_path=cert, key_path=key
    )
    assert (
        callback_response.status_code == 400
    ), f"Expecting error from callback, expected 400 got {callback_response.status_code}"
