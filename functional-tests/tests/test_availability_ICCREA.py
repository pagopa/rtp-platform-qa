import allure
import pytest

from api.debtor_service_provider_api import send_srtp_to_iccrea
from config.configuration import secrets
from utils.dataset import generate_epc_rtp_data
from utils.dataset import generate_rtp_data

@allure.epic('ICCREA Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to ICCREA directly')
@allure.title('An RTP is sent through ICCREA API')
@allure.tag('functional', 'happy_path', 'rtp_send', 'iccrea_availability')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.iccrea
def test_send_rtp_to_iccrea():

    rtp_data = generate_rtp_data(payer_id=secrets.iccrea_activated_fiscal_code)
    iccrea_payload = generate_epc_rtp_data(rtp_data, bic='ICRAITRRXXX')
    response = send_srtp_to_iccrea(iccrea_payload)
    assert response.status_code == 201
