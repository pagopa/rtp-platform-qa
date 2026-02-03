import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender with different statuses')
@allure.title('An UPDATE message with status {status} is successfully sent after CREATE')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'update_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', [
    'VALID',
    'INVALID',
    'PAID',
    'EXPIRED',
    'DRAFT'
])
def test_send_gpd_message_update_scenarios(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status
):
    """Test sending an UPDATE operation message with different statuses via GPD message API after a CREATE"""

    activate_payer(random_fiscal_code)

    create_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation='CREATE',
        status='VALID'
    )

    response_create = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=create_payload
    )

    assert response_create.status_code == 200, (
        f"Expected 200 for CREATE, got {response_create.status_code}. Response: {response_create.text}"
    )

    iuv = create_payload['iuv']
    msg_id = create_payload['id']
    print(f"DEBUG: IUV from CREATE payload: {iuv}")
    print(f"DEBUG: msg_id from CREATE payload: {msg_id}")

    update_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation='UPDATE',
        status=status,
        iuv=iuv,
        msg_id=msg_id
    )
    print(f"DEBUG: IUV in UPDATE payload: {update_payload['iuv']}")
    print(f"DEBUG: msg_id in UPDATE payload: {update_payload['id']}")

    response_update = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=update_payload
    )

    assert response_update.status_code == 200, (
        f"Expected 200 for UPDATE status {status}, got {response_update.status_code}. Response: {response_update.text}"
    )
