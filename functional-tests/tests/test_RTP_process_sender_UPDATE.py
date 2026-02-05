import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_response_code
from utils.test_expectations import UPDATE_EXPECTED_CODES

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender with different statuses')
@allure.title('An UPDATE message with status {status} after CREATE')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'update_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', list(UPDATE_EXPECTED_CODES.keys()))
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

    assert_response_code(response_create, 200, 'CREATE', 'VALID')

    iuv = create_payload['iuv']
    msg_id = create_payload['id']

    update_payload = generate_gpd_message_payload(
        fiscal_code=random_fiscal_code,
        operation='UPDATE',
        status=status,
        iuv=iuv,
        msg_id=msg_id
    )

    response_update = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=update_payload
    )

    expected_code = UPDATE_EXPECTED_CODES[status]
    assert_response_code(response_update, expected_code, 'UPDATE', status)
