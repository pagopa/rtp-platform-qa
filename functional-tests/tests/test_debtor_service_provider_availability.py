import random

import allure
import pytest

from api.auth import get_cbi_access_token
from api.debtor_service_provider import send_srtp_to_cbi
from api.debtor_service_provider import send_srtp_to_iccrea
from api.debtor_service_provider import send_srtp_to_poste
from config.configuration import secrets
from utils.cryptography import client_credentials_to_auth_token
from utils.dataset import generate_epc_rtp_data
from utils.dataset import generate_rtp_data


@allure.feature('Authentication')
@allure.story('Client authenticates to CBI')
@allure.title('Auth endpoint returns valid token')
@pytest.mark.auth
def test_get_cbi_access_token(debtor_sp_mock_cert_key):
    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = debtor_sp_mock_cert_key

    token = get_cbi_access_token(cert, key, auth)
    assert isinstance(token, str) and token


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI directly')
@allure.title('An RTP is sent through CBI API')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi(debtor_sp_mock_cert_key):
    rtp_data = generate_rtp_data()
    cbi_payload = generate_epc_rtp_data(rtp_data, bic='UNCRITMM')

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )

    cert, key = debtor_sp_mock_cert_key

    cbi_token = get_cbi_access_token(cert, key, auth)
    response = send_srtp_to_cbi(f"Bearer {cbi_token}", cbi_payload)
    assert response.status_code == 201


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI')
@allure.title('Cannot send RTP with invalid amount')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi_invalid_amount(debtor_sp_mock_cert_key):
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['amount'] = -1
    cbi_payload = generate_epc_rtp_data(rtp_data, bic='UNCRITMM')

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )

    cert, key = debtor_sp_mock_cert_key

    cbi_token = get_cbi_access_token(cert, key, auth)

    response = send_srtp_to_cbi(f"Bearer {cbi_token}", cbi_payload)
    assert response.status_code == 400


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI')
@allure.title('Cannot send RTP with expired date')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi_expired_date(debtor_sp_mock_cert_key):
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['expiryDate'] = '2020-01-01'
    cbi_payload = generate_epc_rtp_data(rtp_data, bic='UNCRITMM')

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = debtor_sp_mock_cert_key

    cbi_token = get_cbi_access_token(cert, key, auth)

    response = send_srtp_to_cbi(f"Bearer {cbi_token}", cbi_payload)
    assert response.status_code == 400


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


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to ICCREA directly')
@allure.title('An RTP is sent through ICCREA API')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.iccrea
def test_send_rtp_to_iccrea():

    rtp_data = generate_rtp_data(payer_id=secrets.iccrea_activated_fiscal_code)
    iccrea_payload = generate_epc_rtp_data(rtp_data, bic='ICRAITRRXXX')
    response = send_srtp_to_iccrea(iccrea_payload)
    assert response.status_code == 201
