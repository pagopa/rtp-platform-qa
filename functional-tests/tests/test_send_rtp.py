import allure
import pytest

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
    access_token = get_valid_access_token(client_id=secrets.creditor_service_provider.client_id, client_secret=secrets.creditor_service_provider.client_secret)

    response = send_rtp(access_token=access_token, rtp_payload=rtp_data)
    assert response.status_code == 201
