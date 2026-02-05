import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_body_presence
from utils.response_assertions_utils import assert_response_code
from utils.response_assertions_utils import get_response_body_safe
from utils.test_expectations import CREATE_EXPECTED_CODES
from utils.test_expectations import should_have_body

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender with different statuses')
@allure.title('A CREATE message with status {status}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'create_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', list(CREATE_EXPECTED_CODES.keys()))
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

    expected_code = CREATE_EXPECTED_CODES[status]
    assert_response_code(response, expected_code, 'CREATE', status)

    response_body = get_response_body_safe(response)
    assert_body_presence(response_body, should_have_body(status), 'CREATE', status)
