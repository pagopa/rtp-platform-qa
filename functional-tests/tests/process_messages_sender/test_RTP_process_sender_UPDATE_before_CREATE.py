import allure
import pytest

from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_response_code
from utils.test_expectations import UPDATE_BEFORE_CREATE_CODES


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender with different statuses")
@allure.title("An UPDATE message with status {status} before CREATE")
@allure.tag("functional", "gpd_message", "rtp_send", "update_before_create_parameterized")
@pytest.mark.send
@pytest.mark.parametrize("status", list(UPDATE_BEFORE_CREATE_CODES.keys()))
def test_send_gpd_message_update_before_create(rtp_consumer_access_token, random_fiscal_code, activate_payer, status):
    """Test sending an UPDATE operation message with different statuses via GPD message API before a CREATE"""

    activate_payer(random_fiscal_code)

    update_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="UPDATE", status=status)

    response_update = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=update_payload)

    expected_code = UPDATE_BEFORE_CREATE_CODES[status]
    assert_response_code(response_update, expected_code, "UPDATE before CREATE", status)


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends an UPDATE VALID before CREATE")
@allure.title("An UPDATE VALID before CREATE creates the RTP in the database")
@allure.tag("functional", "happy_path", "gpd_message", "rtp_send", "update_before_create_valid")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_update_valid_before_create_rtp_exists(
    rtp_consumer_access_token, rtp_reader_access_token, random_fiscal_code, activate_payer
):
    """UPDATE VALID before any CREATE creates a new RTP; the RTP must be retrievable from the database"""

    activate_payer(random_fiscal_code)

    update_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="UPDATE", status="VALID")
    response_update = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=update_payload)
    assert_response_code(response_update, 200, "UPDATE before CREATE", "VALID")

    response_update_json = response_update.json()
    assert "resourceID" in response_update_json, f"Expected 'resourceID' in response body, got: {response_update.text}"
    resource_id = response_update_json["resourceID"]

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200, f"Expected RTP to exist in DB, got {get_response.status_code}"
    assert get_response.json()["resourceID"] == resource_id
