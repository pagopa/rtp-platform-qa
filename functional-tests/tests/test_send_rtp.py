import allure
import pytest

from api.activation import activate
from api.auth import get_valid_access_token
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset import generate_rtp_data


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('An RTP is sent through API')
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    res = activate(debtor_service_provider_access_token, rtp_data['payerId'],
                   secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == 201


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('Debtor fiscal code must be lower case during RTP send')
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_api():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    res = activate(debtor_service_provider_access_token, rtp_data['payerId'],
                   secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    rtp_data['payerId'] = rtp_data['payerId'].lower()
    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == 422
