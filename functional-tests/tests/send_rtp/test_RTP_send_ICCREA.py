import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from api.RTP_send_api import send_rtp
from config.configuration import config, secrets
from utils.dataset_RTP_data import generate_rtp_data
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.regex_utils import uuidv4_pattern


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider")
@allure.title("An RTP is sent to ICCREA service with activated fiscal code")
@allure.tag("functional", "happy_path", "rtp_send", "iccrea")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.iccrea
def test_send_rtp_to_iccrea(rtp_consumer_access_token):

    message_payload = generate_gpd_message_payload(
        fiscal_code=secrets.iccrea_activated_fiscal_code,
        operation="CREATE",
        status="VALID",
    )

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert bool(uuidv4_pattern.fullmatch(resource_id)), f"resourceId is not a valid UUIDv4: {resource_id}"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider")
@allure.title("An RTP is sent to ICCREA service with activated fiscal code - through Web API")
@allure.tag("functional", "happy_path", "rtp_send", "iccrea")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.iccrea
def test_send_rtp_to_iccrea_THROUGH_WEB_API(creditor_service_provider_token_a):

    rtp_data = generate_rtp_data(payer_id=secrets.iccrea_activated_fiscal_code)

    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert "/".join(location_split[:-1]) == config.rtp_creation_base_url_path + config.send_rtp_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))

