import random

import allure
import pytest

from api.auth_api import get_poste_access_token
from api.debtor_service_provider_api import send_srtp_to_poste
from utils.dataset_EPC_RTP_data import generate_epc_rtp_data
from utils.dataset_RTP_data import generate_rtp_data
from config.configuration import secrets


@allure.epic('Poste Availability')
@allure.feature('Authentication Token Retrieval')
@allure.story('Client authenticates to POSTE')
@allure.title('Auth endpoint returns valid token')
@allure.tag('functional', 'happy_path', 'authentication', 'poste_token')
@pytest.mark.auth
def test_get_poste_access_token(debtor_sp_mock_cert_key):
    """
    Tests the retrieval of an access token from the POSTE authentication endpoint using client credentials and mutual TLS.
    
    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)

    assert isinstance(token, str) and token, "Failed to retrieve a valid access token from POSTE."

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
