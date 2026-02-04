import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_delete_message_payload
from utils.dataset_gpd_message import generate_gpd_message_payload

@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends DELETE message to Sender after CREATE')
@allure.title('A DELETE message after CREATE {status} returns {expected_delete_code}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'delete_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status,expected_delete_code,expect_body', [
    ('VALID', 200, True),
    ('INVALID', 422, False),
    ('PAID', 422, False),
    ('PUBLISHED', 422, False),
    ('EXPIRED', 422, False),
    ('DRAFT', 422, False),
], ids=['VALID', 'INVALID', 'PAID', 'PUBLISHED', 'EXPIRED', 'DRAFT'])
def test_send_gpd_message_delete_after_create(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status,
    expected_delete_code,
    expect_body
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

    expected_create_code = 200 if status == 'VALID' else 400
    assert response_create.status_code == expected_create_code, (
        f"Expected {expected_create_code} for CREATE with status {status}, got {response_create.status_code}. Response: {response_create.text}"
    )

    msg_id = create_payload['id']
    iuv = create_payload['iuv']

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id, iuv=iuv)

    response_delete = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=delete_payload
    )

    assert response_delete.status_code == expected_delete_code, (
        f"Expected {expected_delete_code} for DELETE after CREATE with status {status}, got {response_delete.status_code}. Response: {response_delete.text}"
    )

    response_body = response_delete.json()

    if expect_body:
        assert response_body, (
            f"Expected non-empty body for DELETE after CREATE with status {status}, got empty response"
        )
    else:
        assert not response_body, (
            f"Expected empty body for DELETE after CREATE with status {status}, got: {response_body}"
        )


@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends DELETE message to Sender after CREATE and UPDATE')
@allure.title('A DELETE message after CREATE VALID + UPDATE {status} returns {expected_delete_code}')
@allure.tag('functional', 'gpd_message', 'rtp_send', 'delete_parameterized')
@pytest.mark.send
@pytest.mark.parametrize('status,expected_delete_code', [
    ('VALID', 200),
    ('INVALID', 422),
    ('PAID', 422),
    ('EXPIRED', 422),
    ('DRAFT', 422),
], ids=['VALID', 'INVALID', 'PAID', 'EXPIRED', 'DRAFT'])
def test_send_gpd_message_delete_after_create_and_update(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer,
    status,
    expected_delete_code
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

    assert response_create.status_code == 200, (
        f"Expected 200 for CREATE, got {response_create.status_code}. Response: {response_create.text}"
    )

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

    assert response_update.status_code == 200, (
        f"Expected 200 for UPDATE with status {status}, got {response_update.status_code}. Response: {response_update.text}"
    )

    delete_payload = generate_gpd_delete_message_payload(msg_id=msg_id, iuv=iuv)

    response_delete = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=delete_payload
    )

    assert response_delete.status_code == expected_delete_code, (
        f"Expected {expected_delete_code} for DELETE after UPDATE with status {status}, got {response_delete.status_code}. Response: {response_delete.text}"
    )
