import allure
import pytest
from api.callback import srtp_callback
from utils.dataset import generate_rtp_data


@allure.feature('RTP Callback')
@allure.story('Service provider receives RTP callback')
@allure.title('RTP callback is successfully received')
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_rtp_callback():
    rtp_data = generate_rtp_data()

    activation_response = srtp_callback(rtp_payload=rtp_data)
    assert activation_response.status_code == 200, 'Error from callback'
