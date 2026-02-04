import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_delete_message_payload
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_body_presence
from utils.response_assertions_utils import assert_response_code
from utils.response_assertions_utils import get_response_body_safe
from utils.test_expectations import DELETE_AFTER_CREATE_CODES
from utils.test_expectations import DELETE_AFTER_UPDATE_CODES
from utils.test_expectations import get_create_expected_code
from utils.test_expectations import should_have_body
from utils.test_expectations import UPDATE_EXPECTED_CODES

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends DELETE message to Sender after CREATE')
@allure.title('A DELETE message after CREATE {status} returns {expected_delete_code}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'delete_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', list(DELETE_AFTER_CREATE_CODES.keys()))
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

    expected_create_code = get_create_expected_code(status)
    assert_response_code(response_create, expected_create_code, 'CREATE', status)

    msg_id = create_payload['id']
    iuv = create_payload['iuv']

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id, iuv=iuv)

    response_delete = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=delete_payload
    )

    expected_delete_code = DELETE_AFTER_CREATE_CODES[status]
    assert_response_code(response_delete, expected_delete_code, 'DELETE after CREATE', status)

    response_body = get_response_body_safe(response_delete)
    assert_body_presence(response_body, should_have_body(status), 'DELETE after CREATE', status)


@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends DELETE message to Sender after CREATE and UPDATE')
@allure.title('A DELETE message after CREATE VALID + UPDATE {status} returns {expected_delete_code}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'delete_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status', list(DELETE_AFTER_UPDATE_CODES.keys()))
def test_send_gpd_message_delete_after_create_and_update(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status
):
    """Test sending a DELETE operation message via GPD message API after a CREATE VALID + UPDATE"""

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

    msg_id = create_payload['id']
    iuv = create_payload['iuv']

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

    expected_update_code = UPDATE_EXPECTED_CODES[status]
    assert_response_code(response_update, expected_update_code, 'UPDATE', status)

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id, iuv=iuv)

    response_delete = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=delete_payload
    )

    expected_delete_code = DELETE_AFTER_UPDATE_CODES[status]
    assert_response_code(response_delete, expected_delete_code, 'DELETE after UPDATE', status)
