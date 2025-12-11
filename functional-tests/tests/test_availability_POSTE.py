import random

import allure
import pytest

from utils.dataset_EPC_RTP_data import generate_epc_rtp_data
from utils.dataset_RTP_data import generate_rtp_data
from api.debtor_service_provider_api import send_srtp_to_poste
from utils.dataset_EPC_RTP_data import generate_epc_rtp_data
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE directly')
@allure.title('An RTP is sent through POSTE API')
@allure.tag('functional', 'happy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.poste
def test_send_rtp_to_poste():
    amount = random.randint(100, 10000)
    rtp_data = generate_rtp_data(amount=amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')

    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 201

@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with invalid amount')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_invalid_amount():

    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['amount'] = -1
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 400

@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with an amount over the POSTE limit')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_over_limit_amount():

    over_limit_amount = 1_000_000_000_000
    rtp_data = generate_rtp_data(amount=over_limit_amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 400


@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with expired date')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_expired_date():
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['expiryDate'] = '2020-01-01'
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')

    response = send_srtp_to_poste(poste_payload)
    assert response.status_code == 400
