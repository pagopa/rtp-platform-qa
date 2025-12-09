import random

import allure
import pytest

from api.debtor_service_provider import send_srtp_to_poste
from utils.dataset import generate_epc_rtp_data
from utils.dataset import generate_rtp_data



@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE directly')
@allure.title('An RTP is sent through POSTE API')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.poste
def test_send_rtp_to_poste():
    amount = random.randint(100, 10000)
    rtp_data = generate_rtp_data(amount=amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')

    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 201


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with invalid amount')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_invalid_amount():

    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['amount'] = -1
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 400


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with an amount over the POSTE limit')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_over_limit_amount():

    over_limit_amount = 1_000_000_000_000
    rtp_data = generate_rtp_data(amount=over_limit_amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 400


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with expired date')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_expired_date():
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['expiryDate'] = '2020-01-01'
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')

    response = send_srtp_to_poste(poste_payload)
    assert response.status_code == 400