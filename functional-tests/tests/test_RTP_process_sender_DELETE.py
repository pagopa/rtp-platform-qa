import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_delete_message_payload
from utils.dataset_gpd_message import generate_gpd_message_payload

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends DELETE message to Sender after CREATE')
@allure.title('A DELETE message is successfully sent after CREATE with status {status}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'delete_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', [
    'VALID',
    'INVALID',
    'PAID',
    'EXPIRED',
    'DRAFT'
])
def test_send_gpd_message_delete_after_create(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status
):
    """Test sending a DELETE operation message via GPD message API after a CREATE"""

    activate_payer(random_fiscal_code)

    create_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation='CREATE',
        status=status
    )

    response_create = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=create_payload
    )

    assert response_create.status_code == 200, (
        f"Expected 200 for CREATE, got {response_create.status_code}. Response: {response_create.text}"
    )

    msg_id = create_payload['id']

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id)

    response_delete = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=delete_payload
    )

    assert response_delete.status_code == 200, (
        f"Expected 200 for DELETE after CREATE with status {status}, got {response_delete.status_code}. Response: {response_delete.text}"
    )
