import allure
import pytest

from api.callback import srtp_callback
from config.configuration import config
from config.configuration import secrets
from utils.cryptography import get_serial_from_pem
from utils.cryptography import pfx_to_pem
from utils.dataset import generate_callback_data


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('An RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback():
    callback_data = generate_callback_data()

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    with open(cert, 'rb') as f:
        pem_data = f.read()
        certificate_serial = get_serial_from_pem(pem_data)

    callback_response = srtp_callback(rtp_payload=callback_data,
                                      cert_path=cert,
                                      key_path=key,
                                      certificate_serial=certificate_serial)
    assert callback_response.status_code == 200, f'Error from callback, expected 200 got {callback_response.status_code}'


@allure.feature('RTP Callback')
@allure.story('Service provider sends a callback referred to an RTP')
@allure.title('Unauthorized callback due to wrong certificate serial')
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_fail_send_rtp_callback_wrong_certificate_serial():
    callback_data = generate_callback_data()

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    with open(cert, 'rb') as f:
        pem_data = f.read()
        certificate_serial = get_serial_from_pem(pem_data) + '0'

    callback_response = srtp_callback(rtp_payload=callback_data,
                                      cert_path=cert,
                                      key_path=key,
                                      certificate_serial=certificate_serial)
    assert callback_response.status_code == 403, f'Expecting error from callback, expected 403 got {callback_response.status_code}'
