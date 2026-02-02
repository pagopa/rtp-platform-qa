import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender with different statuses')
@allure.title('A CREATE message with status {status} is successfully sent')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'create_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', [
    'VALID',
    'INVALID',
    'PARTIALLY_PAID',
    'PAID',
    'PUBLISHED',
    'EXPIRED',
    'DRAFT'
])
def test_send_gpd_message_create_scenarios(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status
):
    """Test sending a CREATE operation message with different statuses via GPD message API"""

    activate_payer(random_fiscal_code)

    message_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation='CREATE',
        status=status
    )

    response = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload
    )

    assert response.status_code == 200, (
        f"Expected 200 for status {status}, got {response.status_code}. Response: {response.text}"
    )
