import allure
import pytest

from api.RTP_send_api import send_rtp
from config.configuration import config
from config.configuration import secrets
from utils.dataset import generate_rtp_data
from utils.dataset import uuidv4_pattern

@allure.epic('RTP Send')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to a provider through Sender')
@allure.title('An RTP is sent to a CBI service with activated fiscal code')
@allure.tag('functional', 'happy_path', 'rtp_send', 'cbi')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.cbi
def test_send_rtp_to_cbi(creditor_service_provider_token_a):

    fiscal_code = secrets.cbi_activated_fiscal_code
    payee_id = secrets.cbi_payee_id
    rtp_data = generate_rtp_data(payer_id=fiscal_code, payee_id=str(payee_id))

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a, rtp_payload=rtp_data
    )

    assert send_response.status_code == 201

    location = send_response.headers['Location']
    location_split = location.split('/')
    assert (
        '/'.join(location_split[:-1])
        == config.rtp_creation_base_url_path + config.send_rtp_path
    )
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))
