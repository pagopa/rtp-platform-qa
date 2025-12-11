import random

import allure
import pytest

from api.send_rtp import send_rtp
from config.configuration import config
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data
from utils.regex_utils import uuidv4_pattern

@allure.epic('RTP Send')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to a provider')
@allure.title('An RTP is sent to Poste service with activated fiscal code')
@allure.tag('functional', 'happy_path', 'rtp_send', 'poste')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.poste
def test_send_rtp_to_poste(creditor_service_provider_token_a):

    amount = random.randint(100, 10000)
    rtp_data = generate_rtp_data(
        payer_id=secrets.poste_activated_fiscal_code, amount=amount
    )

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
