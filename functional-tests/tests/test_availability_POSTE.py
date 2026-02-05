import random
from typing import Tuple

import allure
import pytest

from api.auth_api import get_poste_access_token
from api.debtor_service_provider_api import send_srtp_to_poste
from config.configuration import secrets
from utils.dataset_EPC_RTP_data import generate_epc_rtp_data
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic('Poste Availability')
@allure.feature('Authentication Token Retrieval')
@allure.story('Client authenticates to POSTE')
@allure.title('Auth endpoint returns valid token')
@allure.tag('functional', 'happy_path', 'authentication', 'poste_token')
@pytest.mark.auth
def test_get_poste_access_token(debtor_sp_mock_cert_key: Tuple[str, str]):
    """
    Tests the retrieval of an access token from the POSTE authentication endpoint using client credentials and mutual TLS.

    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)

    assert isinstance(token, str) and token, 'Failed to retrieve a valid access token from POSTE.'

@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE directly')
@allure.title('An RTP is sent through POSTE API')
@allure.tag('functional', 'happy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.poste
def test_send_rtp_to_poste(debtor_sp_mock_cert_key: Tuple[str, str]):
    """
    Tests sending an RTP payload to the POSTE endpoint with valid data and authentication.

    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    amount = random.randint(100, 10000)
    rtp_data = generate_rtp_data(amount=amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)

    response = send_srtp_to_poste(token, poste_payload)

    assert response.status_code == 201

@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with invalid amount')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_invalid_amount(debtor_sp_mock_cert_key: Tuple[str, str]):
    """
    Tests that sending an RTP payload with an invalid amount to the POSTE endpoint results in a 400 Bad Request response.

    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['amount'] = -1
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)
    response = send_srtp_to_poste(token, poste_payload)

    assert response.status_code == 400

@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with an amount over the POSTE limit')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_over_limit_amount(debtor_sp_mock_cert_key: Tuple[str, str]):
    """
    Tests that sending an RTP payload with an amount over the POSTE limit results in a 400 Bad Request response.

    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    over_limit_amount = 1_000_000_000_000
    rtp_data = generate_rtp_data(amount=over_limit_amount)
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)

    response = send_srtp_to_poste(token, poste_payload)

    assert response.status_code == 400


@allure.epic('POSTE Availability')
@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to POSTE')
@allure.title('Cannot send RTP with expired date')
@allure.tag('functional', 'unhappy_path', 'rtp_send', 'poste_availability')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.poste
def test_send_rtp_to_poste_expired_date(debtor_sp_mock_cert_key: Tuple[str, str]):
    """
    Tests that sending an RTP payload with an expired date to the POSTE endpoint results in a 400 Bad Request response.

    :param debtor_sp_mock_cert_key: Certificate and key tuple for mutual TLS authentication.
    :type debtor_sp_mock_cert_key: Tuple[str, str]
    """
    cert, key = debtor_sp_mock_cert_key

    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['expiryDate'] = '2020-01-01'
    poste_payload = generate_epc_rtp_data(rtp_data, bic='PPAYITR1XXX')
    token = get_poste_access_token(
        cert, key, secrets.poste_oauth.client_id, secrets.poste_oauth.client_secret)

    response = send_srtp_to_poste(token, poste_payload)
    assert response.status_code == 400
