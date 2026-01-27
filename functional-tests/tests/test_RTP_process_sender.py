import allure
import pytest

from api.RTP_process_sender import send_gpd_message


def generate_gpd_message_payload(fiscal_code: str, operation: str = "CREATE"):
    """Generate a valid GPD message payload using the exact structure from the curl example"""
    payload = {
        "id": 5780880355709746,
        "operation": operation,
        "timestamp": 1769422334273,
        "iuv": "97704563415785664",
        "subject": "remittanceInformation 1",
        "description": "Canone Unico Patrimoniale - CORPORATE - TEST",
        "ec_tax_code": "80015010723",
        "debtor_tax_code": fiscal_code,
        "nav": "397704563415785664",
        "due_date": 1761815347153000,
        "amount": 30000,
        "status": "VALID",
        "psp_code": None,
        "psp_tax_code": None
    }
    
    return payload


@allure.epic('RTP GPD Message')
@allure.feature('GPD Message API')
@allure.story('Consumer sends RTP message to Sender')
@allure.title('A CREATE message is successfully sent through GPD message API')
@allure.tag('functional', 'happy_path', 'gpd_message', 'rtp_send')
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create(
    rtp_consumer_access_token,
    random_fiscal_code,
    activate_payer
):
    """Test sending a CREATE operation message via GPD message API"""
    
    activate_payer(random_fiscal_code)
    
    message_payload = generate_gpd_message_payload(random_fiscal_code, "CREATE")
    
    response = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload
    )
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
