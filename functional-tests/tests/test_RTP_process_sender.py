import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender')
@allure.title('A CREATE message is successfully sent through GPD message API')
@allure.tag('functional', 'happy_path', 'gpd_message', 'rtp_send')
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer
):
    """Test sending a CREATE operation message via GPD message API"""

    activate_payer(random_fiscal_code)

    message_payload = generate_gpd_message_payload(random_fiscal_code, 'CREATE')

    response = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
