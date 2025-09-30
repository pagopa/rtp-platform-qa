import time
from datetime import datetime
from datetime import timezone

import allure
import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.get_rtp import get_rtp_by_notice_number
from api.producer_gpd_message import send_producer_gpd_message
from config.configuration import config
from config.configuration import secrets
from utils.dataset import generate_rtp_data
from utils.producer_gpp_dataset import generate_producer_gpd_message_payload

TEST_TIMEOUT_SEC = config.test_timeout_sec
POLLING_RATE_SEC = 30

# Primo test invariato
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


@allure.feature('Producer Message')
@allure.story('Send producer message with invalid payee')
@allure.title('Send message with invalid payee_name and verify rejection and no RTP creation')
@pytest.mark.producer_gpd_message
@pytest.mark.unhappy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_send_producer_gpd_message_invalid_payee():
    invalid_payee_name = 'InvalidPayee'
    rtp_data = generate_rtp_data()

    if 'paymentOption' in rtp_data and len(rtp_data['paymentOption']) > 0:
        nav = rtp_data['paymentOption'][0].get('nav')
    elif 'notice_number' in rtp_data:
        nav = f"3{rtp_data['notice_number']}"
    else:
        from utils.generators import generate_notice_number
        notice_number = generate_notice_number()
        nav = f"3{notice_number}"
        rtp_data['notice_number'] = notice_number

    payload = {
        'payee_name': invalid_payee_name,
        'nav': nav,
        **rtp_data
    }

    response = send_producer_gpd_message(payload)
    assert response.status_code in [400, 422], f"Expected error status for invalid payee: {response.status_code}, {response.text}"

    access_token = _get_rtp_reader_access_token()

    start_time = time.time()
    max_polling_time = TEST_TIMEOUT_SEC - 30

    while time.time() - start_time < max_polling_time:
        response = get_rtp_by_notice_number(access_token, nav)

        if response.status_code != 200 and response.status_code != 404:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {nav}"
            )

        if response.status_code == 404:
            break

        data = response.json()
        assert isinstance(data, list), 'Invalid response body.'

        if len(data) > 0:
            pytest.fail(f"RTP should not be created for invalid payee: {data}")

        time.sleep(POLLING_RATE_SEC)
