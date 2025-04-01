import allure
import pytest

from api.callback import srtp_callback
from config.configuration import config
from config.configuration import secrets
from utils.cryptography import pfx_to_pem
from utils.dataset import generate_rtp_data


@allure.feature('RTP Callback')
@allure.story('Service provider receives RTP callback')
@allure.title('RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback():
    rtp_data = generate_rtp_data()

    cert, key = pfx_to_pem(secrets.debtor_service_provider_mock_PFX_base64,
                           secrets.debtor_service_provider_mock_PFX_password_base64,
                           config.cert_path,
                           config.key_path)

    activation_response = srtp_callback(rtp_payload=rtp_data, cert_path=cert, key_path=key)
    assert activation_response.status_code == 200, 'Error from callback'
