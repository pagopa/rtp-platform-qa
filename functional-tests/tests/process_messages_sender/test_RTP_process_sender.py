import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender")
@allure.title("A CREATE message is successfully sent through GPD message API")
@allure.tag("functional", "happy_path", "gpd_message", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create(rtp_consumer_access_token, random_fiscal_code, activate_payer):
    """Test sending a CREATE operation message via GPD message API"""

    activate_payer(random_fiscal_code)

    message_payload = generate_gpd_message_payload(random_fiscal_code, "CREATE")

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender")
@allure.title("A CREATE message with omocodia fiscal code is successfully sent through GPD message API")
@allure.tag("functional", "happy_path", "gpd_message", "rtp_send", "omocodia")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create_omocodia_fiscal_code(
    rtp_consumer_access_token, random_omocodia_fiscal_code, activate_payer
):
    """Test sending a CREATE operation message with an omocodia fiscal code via GPD message API"""

    activate_payer(random_omocodia_fiscal_code)

    message_payload = generate_gpd_message_payload(random_omocodia_fiscal_code, "CREATE")

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender")
@allure.title("A CREATE message with foreign fiscal code is successfully sent through GPD message API")
@allure.tag("functional", "happy_path", "gpd_message", "rtp_send", "foreign")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create_foreign_fiscal_code(
    rtp_consumer_access_token, random_foreign_fiscal_code, activate_payer
):
    """Test sending a CREATE operation message with a foreign fiscal code via GPD message API"""

    activate_payer(random_foreign_fiscal_code)

    message_payload = generate_gpd_message_payload(random_foreign_fiscal_code, "CREATE")

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Consumer sends RTP message to Sender")
@allure.title("A CREATE message with VAT number (Partita IVA) is successfully sent through GPD message API")
@allure.tag("functional", "happy_path", "gpd_message", "rtp_send", "vat")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create_vat_number(rtp_consumer_access_token, random_vat_number, activate_payer):
    """Test sending a CREATE operation message with an Italian VAT number via GPD message API"""

    activate_payer(random_vat_number)

    message_payload = generate_gpd_message_payload(random_vat_number, "CREATE")

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
