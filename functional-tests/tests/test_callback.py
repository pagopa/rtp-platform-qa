import allure
import pytest

from api.callback import srtp_callback
from config.configuration import config
from config.configuration import secrets
from utils.cryptography import pfx_to_pem
from utils.dataset import generate_callback_data_DS_04b_compliant
from utils.dataset import generate_static_callback_data_DS_08P_compliant


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_04b_compliant():
    callback_data = generate_callback_data_DS_04b_compliant()

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    callback_response = srtp_callback(rtp_payload=callback_data,
                                      cert_path=cert,
                                      key_path=key)
    assert callback_response.status_code == 200, f'Error from callback, expected 200 got {callback_response.status_code}'


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback_DS_08P_compliant():
    callback_data = generate_static_callback_data_DS_08P_compliant()

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    callback_response = srtp_callback(rtp_payload=callback_data,
                                      cert_path=cert,
                                      key_path=key)
    assert callback_response.status_code == 200, f'Error from callback, expected 200 got {callback_response.status_code}'


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial_DS_04b_compliant():
    callback_data = generate_callback_data_DS_04b_compliant(BIC='MOCKSP01')

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    callback_response = srtp_callback(rtp_payload=callback_data,
                                      cert_path=cert,
                                      key_path=key)
    assert callback_response.status_code == 403, f'Expecting error from callback, expected 403 got {callback_response.status_code}'
