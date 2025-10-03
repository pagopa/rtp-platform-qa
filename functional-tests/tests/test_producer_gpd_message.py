import time
from datetime import datetime
from datetime import timezone

import allure
import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.activation import activate
from api.get_rtp import get_rtp_by_notice_number
from api.payee_registry import get_payee_registry
from api.producer_gpd_message import send_producer_gpd_message
from config.configuration import config
from config.configuration import secrets
from utils.dataset import generate_rtp_data
from utils.generators import generate_notice_number
from utils.producer_gpp_dataset import generate_producer_gpd_message_payload
from utils.fiscal_code_utils import fake_fc 

TEST_TIMEOUT_SEC = config.test_timeout_sec
POLLING_RATE_SEC = 30

def _send_message_with_retry(payload, message_label='', max_retries=3, retry_delay=5):
    """Helper function to send a message with retry mechanism"""
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
            pytest.fail('No RTP found, not even for the first message')

        data = response.json()
        assert isinstance(data, list), 'Invalid response body.'

        if len(data) > 1:
            second_message_processed = True
            break

        if time.time() - start_time > 30 and len(data) == 1:
            print('Found only one RTP (first message): the second message has been correctly discarded')
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


def _activate_new_debtor() -> str:
    """
    Generate a new fiscal code and activate it with the debtor service provider.
    
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
    
    debtor_fc = fake_fc()
    print(f"Generated new fiscal code: {debtor_fc}")
    
    activation_response = activate(
        debtor_service_provider_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, f"Failed to activate debtor: {activation_response.status_code}, {activation_response.text}"
    print(f"Successfully activated debtor with fiscal code: {debtor_fc}")
    
    return debtor_fc


@allure.feature('GPD Message')
@allure.story('Send GPD message to queue')
@allure.title('Send two GPD messages with timestamps T1 and T1-T2')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
def test_send_producer_gpd_messages_with_timestamps():
    debtor_fc = _activate_new_debtor()
    
    common_iuv = ''.join('12345678901234567')
    common_notice_number = generate_notice_number()
    common_nav = f"3{common_notice_number}"

    t1 = int(datetime.now(timezone.utc).timestamp() * 1000)

    payload_t1 = generate_producer_gpd_message_payload(
        operation='CREATE',
        ec_tax_code='80015010723',
        amount=30000,
        status='VALID',
        overrides={
            'timestamp': t1,
            'iuv': common_iuv,
            'nav': common_nav,
            'debtor_tax_code': debtor_fc
        }
    )

    response_t1 = _send_message_with_retry(payload_t1, 'first')
    body_t1 = response_t1.json()
    assert body_t1.get('status') == 'success', f"Unexpected response for T1: {body_t1}"

    time.sleep(3)

    t2_offset = 5000
    t1_minus_t2 = t1 - t2_offset

    payload_t1_minus_t2 = generate_producer_gpd_message_payload(
        operation='CREATE',
        ec_tax_code='80015010723',
        amount=30000,
        status='VALID',
        overrides={
            'timestamp': t1_minus_t2,
            'iuv': common_iuv,
            'nav': common_nav,
            'debtor_tax_code': debtor_fc
        }
    )

    response_t1_minus_t2 = _send_message_with_retry(payload_t1_minus_t2, 'second')
    print(f"Response second message: Status {response_t1_minus_t2.status_code}, Body: {response_t1_minus_t2.text}")

    access_token = _get_rtp_reader_access_token()
    max_polling_time = TEST_TIMEOUT_SEC - 30
    second_message_processed = _verify_message_processing(access_token, common_nav, max_polling_time)

    assert not second_message_processed, 'The second message with the previous timestamp should not be processed'
    print('Test completed successfully: the message with the previous timestamp has been correctly discarded')




@allure.feature('GPD Message')
@allure.story('Send GPD message to queue with invalid payee')
@allure.title('Send GPD message with invalid payee_id and verify no RTP is created')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_send_producer_gpd_message_invalid_registry_payee():
    debtor_fc = _activate_new_debtor()

    invalid_payee_id = '80015060728' # length = 11 || 16

    common_iuv = '12445678901294067'
    common_nav = f"3{common_iuv}"

    timestamp = 1768442371790

    payload = generate_producer_gpd_message_payload(
        operation='CREATE',
        ec_tax_code=invalid_payee_id,
        amount=30000,
        status='VALID',
        overrides={
            'iuv': common_iuv,
            'nav': common_nav,
            'timestamp': timestamp,
            'debtor_tax_code': debtor_fc
        }
    )

    response = _send_message_with_retry(payload, 'valid_payee')
    assert response.status_code == 200, f"Failed to send GPD message: {response.status_code}, {response.text}"
    body = response.json()
    assert body.get('status') == 'success', f"Unexpected response: {body}"

    reader_token = _get_rtp_reader_access_token()

    start_time = time.time()
    max_polling_time = TEST_TIMEOUT_SEC - 30
    rtp_found = False


    while time.time() - start_time < max_polling_time:
        response = get_rtp_by_notice_number(reader_token, common_nav)

        if response.status_code != 200 and response.status_code != 404:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {common_nav}"
            )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), 'Invalid response body.'

            if len(data) > 0:
                print(f"RTP found after {int(time.time() - start_time)} seconds")
                rtp_found = True

                break

        time.sleep(POLLING_RATE_SEC)

    assert not rtp_found, 'RTP was unexpectedly created with an invalid payee ID'

    if not rtp_found:
        print('Test completed successfully: no RTP was created with invalid payee ID')


@allure.feature('GPD Message')
@allure.story('Send GPD message to queue with valid payee from registry')
@allure.title('Send GPD message with registry payee_id and verify RTP creation')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_send_producer_gpd_message_valid_registry_payee():
    debtor_fc = _activate_new_debtor()

    payee_registry_token = get_valid_access_token(
        client_id=secrets.pagopa_integration_payee_registry.client_id,
        client_secret=secrets.pagopa_integration_payee_registry.client_secret,
        access_token_function=get_access_token
    )
    
    payee_response = get_payee_registry(payee_registry_token)
    assert payee_response.status_code == 200, f"Failed to get payees: {payee_response.text}"

    payees_data = payee_response.json()
    assert 'payees' in payees_data and len(payees_data['payees']) > 0, 'No payees found in registry'

    registry_payees = payees_data['payees']
    registry_payee_id = None

    for payee in registry_payees:
        if payee['payeeId'] == '80015010723':
            registry_payee_id = payee['payeeId']
            print(f"Found known working payee ID in registry: {registry_payee_id}")
            break

    if not registry_payee_id:
        registry_payee_id = registry_payees[0]['payeeId']
        print(f"Using first payee ID from registry: {registry_payee_id}")

    common_iuv = '12445678901234067'
    common_nav = f"3{common_iuv}"
    print(f"Generated NAV: {common_nav}")

    timestamp = 1768442371790 + 10000000
    print(f"Using timestamp: {timestamp}")

    payload = generate_producer_gpd_message_payload(
        operation='CREATE',
        ec_tax_code=registry_payee_id,
        amount=30000,
        status='VALID',
        overrides={
            'iuv': common_iuv,
            'nav': common_nav,
            'timestamp': timestamp,
            'debtor_tax_code': debtor_fc
        }
    )

    print(f"Sending payload with payee ID: {registry_payee_id} and debtor fiscal code: {debtor_fc}")
    response = _send_message_with_retry(payload, 'registry_payee')
    assert response.status_code == 200, f"Failed to send GPD message: {response.status_code}, {response.text}"
    body = response.json()
    assert body.get('status') == 'success', f"Unexpected response: {body}"

    reader_token = _get_rtp_reader_access_token()

    polling_interval = 10

    start_time = time.time()
    max_polling_time = TEST_TIMEOUT_SEC - 30
    rtp_found = False

    print(f"Polling for RTP creation with nav={common_nav}...")

    while time.time() - start_time < max_polling_time:
        elapsed = int(time.time() - start_time)
        print(f"Polling attempt at {elapsed}s...")

        response = get_rtp_by_notice_number(reader_token, common_nav)
        print(f"Response status: {response.status_code}")

        if response.status_code != 200 and response.status_code != 404:
            raise RuntimeError(
                f"Error calling find_rtp_by_notice_number API. "
                f"Response {response.status_code}. Notice number: {common_nav}"
            )

        if response.status_code == 200:
            data = response.json()
            print(f"Response data length: {len(data)}")
            assert isinstance(data, list), 'Invalid response body.'

            if len(data) > 0:
                print(f"RTP found after {elapsed} seconds")
                rtp_found = True

                rtp = data[0]
                print(f"RTP status: {rtp.get('status', 'NO STATUS')}")
                print(f"RTP notice number: {rtp['noticeNumber']}")
                print(f"RTP payee ID: {rtp['payeeId']}")

                assert rtp['payeeId'] == registry_payee_id, f"Unexpected payee ID: {rtp['payeeId']}"
                assert rtp['noticeNumber'] == common_nav, f"Unexpected notice number: {rtp['noticeNumber']}"

                break

        time.sleep(polling_interval)

    assert rtp_found, f"RTP was not created within the timeout period ({max_polling_time} seconds)"
    print('Test completed successfully: RTP was properly created with registry payee ID')
