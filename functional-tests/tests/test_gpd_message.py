import time
import allure
import pytest
from datetime import datetime, timezone

from api.producer_gpd_message import send_producer_gpd_message
from utils.gpp_dataset import generate_producer_gpd_message_payload

@allure.feature('GPD Message')
@allure.story('Send GPD message to queue')
@allure.title('Send two GPD messages with timestamps T1 and T1-T2')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
def test_send_producer_gpd_messages_with_timestamps():
    t1 = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    t2_offset = 1000
    t1_minus_t2 = t1 - t2_offset
    
    payload_t1 = generate_producer_gpd_message_payload({'timestamp': t1})

    response_t1 = send_producer_gpd_message(payload_t1)
    assert response_t1.status_code == 200, f"Failed to send message with T1: {response_t1.text}"
    
    time.sleep(1)
    
    payload_t1_minus_t2 = generate_producer_gpd_message_payload({'timestamp': t1_minus_t2})

    response_t1_minus_t2 = send_producer_gpd_message(payload_t1_minus_t2)
    assert response_t1_minus_t2.status_code == 200, f"Failed to send message with T1-T2: {response_t1_minus_t2.text}"
    
    body_t1 = response_t1.json()
    assert body_t1.get('status') == 'success', f"Unexpected response for T1: {body_t1}"
    
    body_t1_minus_t2 = response_t1_minus_t2.json()
    assert body_t1_minus_t2.get('status') == 'success', f"Unexpected response for T1-T2: {body_t1_minus_t2}"