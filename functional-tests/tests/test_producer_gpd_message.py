import time
import allure
import pytest
from datetime import datetime, timezone

from config.configuration import config
from config.configuration import secrets
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.get_rtp import get_rtp_by_notice_number
from .generators import generate_notice_number
from api.producer_gpd_message import send_producer_gpd_message
from utils.producer_gpp_dataset import generate_producer_gpd_message_payload

TEST_TIMEOUT_SEC = config.test_timeout_sec
POLLING_RATE_SEC = 30

def _send_message_with_retry(payload, message_label="", max_retries=3, retry_delay=5):
    """Helper function to send a message with retry mechanism"""
    for attempt in range(max_retries):
        try:
            print(f"Sending {message_label} message (attempt {attempt+1}/{max_retries})...")
            response = send_producer_gpd_message(payload)
            
            if response.status_code == 200:
                print(f"{message_label} message sent successfully")
                return response
            elif "RequestTimedOutError" in response.text:
                print(f"Timeout detected: {response.text}")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                continue
            else:
                assert response.status_code == 200, f"Failed to send {message_label} message: {response.text}"
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error sending: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise
    
    pytest.fail(f"Failed to send {message_label} message after {max_retries} attempts")


def _verify_message_processing(access_token, nav, max_polling_time):
    """Helper function to verify message processing status"""
    start_time = time.time()
    second_message_processed = False
    
    print(f"Verify that the RTP for the message with the previous timestamp has NOT been created (nav={nav})")
    
    while time.time() - start_time < max_polling_time:
        response = get_rtp_by_notice_number(access_token, nav)
        
        if response.status_code != 200 and response.status_code != 404:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {nav}"
            )
        
        if response.status_code == 404:
            pytest.fail("No RTP found, not even for the first message")
            
        data = response.json()
        assert isinstance(data, list), 'Invalid response body.'
        
        if len(data) > 1:
            second_message_processed = True
            break
            
        if time.time() - start_time > 30 and len(data) == 1:
            print("Found only one RTP (first message): the second message has been correctly discarded")
            break
        
        time.sleep(POLLING_RATE_SEC)
    
    return second_message_processed

def _get_rtp_reader_access_token() -> str:
    """
    Retrieve a valid access token for the RTP reader client.

    Returns:
        str: A non-empty access token string.

    Raises:
        AssertionError: If no token is retrieved.
    """
    client_id = secrets.rtp_reader.client_id
    client_secret = secrets.rtp_reader.client_secret

    access_token = get_valid_access_token(
        client_id=client_id,
        client_secret=client_secret,
        access_token_function=get_access_token,
    )
    assert access_token is not None, 'Access token cannot be None'
    return access_token


@allure.feature('GPD Message')
@allure.story('Send GPD message to queue')
@allure.title('Send two GPD messages with timestamps T1 and T1-T2')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
def test_send_producer_gpd_messages_with_timestamps():
    common_iuv = ''.join('12345678901234567')
    common_notice_number = generate_notice_number()
    common_nav = f"3{common_notice_number}"
    
    t1 = int(datetime.now(timezone.utc).timestamp() * 1000)
    payload_t1 = generate_producer_gpd_message_payload({
        'timestamp': t1,
        'iuv': common_iuv,
        'nav': common_nav
    })
    
    response_t1 = _send_message_with_retry(payload_t1, "first")
    body_t1 = response_t1.json()
    assert body_t1.get('status') == 'success', f"Unexpected response for T1: {body_t1}"
    
    time.sleep(3)
    
    t2_offset = 5000
    t1_minus_t2 = t1 - t2_offset
    payload_t1_minus_t2 = generate_producer_gpd_message_payload({
        'timestamp': t1_minus_t2,
        'iuv': common_iuv,
        'nav': common_nav
    })
    
    response_t1_minus_t2 = _send_message_with_retry(payload_t1_minus_t2, "second")
    print(f"Response second message: Status {response_t1_minus_t2.status_code}, Body: {response_t1_minus_t2.text}")
    
    access_token = _get_rtp_reader_access_token()
    max_polling_time = TEST_TIMEOUT_SEC - 30
    second_message_processed = _verify_message_processing(access_token, common_nav, max_polling_time)
    
    assert not second_message_processed, "The second message with the previous timestamp should not be processed"
    print("Test completed successfully: the message with the previous timestamp has been correctly discarded")
