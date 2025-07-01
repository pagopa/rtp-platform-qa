import random
import allure
import pytest

from api.auth import get_cbi_access_token
from api.debtor_service_provider import send_srtp_to_cbi
from api.debtor_service_provider import send_srtp_to_poste
from config.configuration import config
from config.configuration import secrets
from utils.cryptography import client_credentials_to_auth_token
from utils.cryptography import pfx_to_pem
from utils.dataset import generate_cbi_rtp_data
from utils.dataset import generate_rtp_data


@allure.feature('Authentication')
@allure.story('Client authenticates to CBI')
@allure.title('Auth endpoint returns valid token')
@pytest.mark.auth
def test_get_cbi_access_token():
    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = pfx_to_pem(
        secrets.CBI_client_PFX_base64,
        secrets.CBI_client_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )
    token = get_cbi_access_token(cert, key, auth)
    assert isinstance(token, str) and token


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI directly')
@allure.title('An RTP is sent through CBI API')
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi():
    rtp_data = generate_rtp_data()
    cbi_payload = generate_cbi_rtp_data(rtp_data)

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = pfx_to_pem(
        secrets.CBI_client_PFX_base64,
        secrets.CBI_client_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )
    cbi_token = get_cbi_access_token(cert, key, auth)

    response = send_srtp_to_cbi(f"Bearer {cbi_token}", cbi_payload)

    assert response.status_code == 201


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI')
@allure.title('Cannot send RTP with invalid amount')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi_invalid_amount():
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['amount'] = -1
    cbi_payload = generate_cbi_rtp_data(rtp_data)

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = pfx_to_pem(
        secrets.CBI_client_PFX_base64,
        secrets.CBI_client_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )
    cbi_token = get_cbi_access_token(cert, key, auth)

    response = send_srtp_to_cbi(f"Bearer {cbi_token}", cbi_payload)
    assert response.status_code == 400


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP to CBI')
@allure.title('Cannot send RTP with expired date')
@pytest.mark.send
@pytest.mark.unhappy_path
@pytest.mark.cbi
def test_send_rtp_to_cbi_expired_date():
    rtp_data = generate_rtp_data()
    rtp_data['paymentNotice']['expiryDate'] = '2020-01-01'
    cbi_payload = generate_cbi_rtp_data(rtp_data)

    auth = client_credentials_to_auth_token(
        secrets.CBI_client_id, secrets.CBI_client_secret
    )
    cert, key = pfx_to_pem(
        secrets.CBI_client_PFX_base64,
        secrets.CBI_client_PFX_password_base64,
        config.cert_path,
        config.key_path,
    )
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
    poste_payload = generate_cbi_rtp_data(rtp_data, bic='PPAYITR1XXX')

    response = send_srtp_to_poste(poste_payload)

    assert response.status_code == 201
