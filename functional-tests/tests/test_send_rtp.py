import allure
import pytest

from api.send_rtp import send_rtp
from utils.dataset import generate_rtp_data


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('An RTP is sent through API')
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api():
    rtp_data = generate_rtp_data()

    response = send_rtp(rtp_data)
    assert response.status_code == 200
