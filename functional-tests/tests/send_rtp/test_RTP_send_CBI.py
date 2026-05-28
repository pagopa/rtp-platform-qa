import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from config.configuration import secrets
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.regex_utils import uuidv4_pattern


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider through Sender")
@allure.title("An RTP is sent to a CBI service with activated fiscal code")
@allure.tag("functional", "happy_path", "rtp_send", "cbi")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.cbi
def test_send_rtp_to_cbi(rtp_consumer_access_token):

    message_payload = generate_gpd_message_payload(
        fiscal_code=secrets.cbi_activated_fiscal_code,
        operation="CREATE",
        status="VALID",
    )

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert bool(uuidv4_pattern.fullmatch(resource_id)), f"resourceId is not a valid UUIDv4: {resource_id}"

