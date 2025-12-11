import time

import pytest

from api.debtor_activation_api import activate
from api.auth_api import get_access_token
from api.auth_api import get_valid_access_token
from api.RTP_get_api import get_rtp_by_notice_number
from api.producer_gpd_message import send_producer_gpd_message
from config.configuration import secrets
from utils.fiscal_code_utils import fake_fc


def send_message_with_retry(payload, message_label='', max_retries=3, retry_delay=5):
    """Helper function to send a GPD message with retry mechanism.

    Args:
        payload (dict): The message payload to send
        message_label (str): A label for the message for logging purposes
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Seconds to wait between retry attempts

    Returns:
        requests.Response: The API response if successful

    Raises:
        AssertionError: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            print(f"Sending {message_label} message (attempt {attempt+1}/{max_retries})...")
            response = send_producer_gpd_message(payload)

            if response.status_code == 200:
                print(f"{message_label} message sent successfully")
                return response
            elif 'RequestTimedOutError' in response.text:
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

    pytest.fail(f"Failed to send {message_label} message after {max_retries} attempts")


def verify_message_processing(access_token, nav, max_polling_time, polling_rate_sec=30):
    """Helper function to verify message processing status.

    Args:
        access_token (str): The access token for RTP API
        nav (str): Notice Number to query
        max_polling_time (int): Maximum time to poll in seconds
        polling_rate_sec (int): Polling interval in seconds

    Returns:
        bool: True if second message was processed, False otherwise
    """
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
            pytest.fail('No RTP found, not even for the first message')

        data = response.json()
        assert isinstance(data, list), 'Invalid response body.'

        if len(data) > 1:
            second_message_processed = True
            break

        if time.time() - start_time > 30 and len(data) == 1:
            print('Found only one RTP (first message): the second message has been correctly discarded')
            break

        time.sleep(polling_rate_sec)

    return second_message_processed


def get_rtp_reader_access_token() -> str:
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


def generate_fiscal_code() -> str:
    """
    Generate a new random fiscal code using the faker library.

    Returns:
        str: A new randomly generated fiscal code
    """
    debtor_fc = fake_fc()
    print(f"Generated new fiscal code: {debtor_fc}")
    return debtor_fc


def activate_debtor(fiscal_code: str) -> str:
    """
    Activate a given fiscal code with the debtor service provider.

    Args:
        fiscal_code (str): The fiscal code to activate

    Returns:
        str: The activated fiscal code

    Raises:
        AssertionError: If activation fails
    """
    debtor_service_provider_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    activation_response = activate(
        debtor_service_provider_token,
        fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, f"Failed to activate debtor: {activation_response.status_code}, {activation_response.text}"
    print(f"Successfully activated debtor with fiscal code: {fiscal_code}")

    return fiscal_code


def activate_new_debtor() -> str:
    """
    Generate a new fiscal code and activate it with the debtor service provider.
    This is a convenience function that combines generate_fiscal_code() and activate_debtor().

    Returns:
        str: The activated fiscal code

    Raises:
        AssertionError: If activation fails
    """
    fiscal_code = generate_fiscal_code()
    return activate_debtor(fiscal_code)
