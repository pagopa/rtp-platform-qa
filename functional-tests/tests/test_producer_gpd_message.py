import time
from datetime import datetime
from datetime import timezone

import allure
import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.get_rtp import get_rtp_by_notice_number
from api.payee_registry import get_payee_registry
from config.configuration import config
from config.configuration import secrets
from utils.generators import generate_iuv
from utils.producer_gpd_utils import activate_new_debtor
from utils.producer_gpd_utils import get_rtp_reader_access_token
from utils.producer_gpd_utils import send_message_with_retry
from utils.producer_gpd_utils import verify_message_processing
from utils.producer_gpp_dataset import generate_producer_gpd_message_payload

TEST_TIMEOUT_SEC = config.test_timeout_sec
POLLING_RATE_SEC = 30

@allure.feature('GPD Message')
@allure.story('Send GPD message to queue')
@allure.title('Send two GPD messages with timestamps T1 and T1-T2')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
def test_send_producer_gpd_messages_with_timestamps():
    debtor_fc = activate_new_debtor()

    common_iuv = generate_iuv()
    common_nav = f"3{common_iuv}"

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

    response_t1 = send_message_with_retry(payload_t1, 'first')
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

    response_t1_minus_t2 = send_message_with_retry(payload_t1_minus_t2, 'second')
    print(f"Response second message: Status {response_t1_minus_t2.status_code}, Body: {response_t1_minus_t2.text}")

    access_token = get_rtp_reader_access_token()
    max_polling_time = TEST_TIMEOUT_SEC - 30
    second_message_processed = verify_message_processing(access_token, common_nav, max_polling_time)

    assert not second_message_processed, 'The second message with the previous timestamp should not be processed'
    print('Test completed successfully: the message with the previous timestamp has been correctly discarded')


@allure.feature('GPD Message')
@allure.story('Send GPD message to queue with invalid payee')
@allure.title('Send GPD message with invalid payee_id and verify no RTP is created')
@pytest.mark.producer_gpd_message
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_send_producer_gpd_message_invalid_registry_payee():
    debtor_fc = activate_new_debtor()

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

    response = send_message_with_retry(payload, 'valid_payee')
    assert response.status_code == 200, f"Failed to send GPD message: {response.status_code}, {response.text}"
    body = response.json()
    assert body.get('status') == 'success', f"Unexpected response: {body}"

    reader_token = get_rtp_reader_access_token()

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

    debtor_fc = activate_new_debtor()

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
            break

    if not registry_payee_id:
        registry_payee_id = registry_payees[0]['payeeId']

    common_iuv = '12445678901234067'
    common_nav = f"3{common_iuv}"

    timestamp = 1768442371790 + 10000000

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

    response = send_message_with_retry(payload, 'registry_payee')
    assert response.status_code == 200, f"Failed to send GPD message: {response.status_code}, {response.text}"
    body = response.json()
    assert body.get('status') == 'success', f"Unexpected response: {body}"

    reader_token = get_rtp_reader_access_token()

    polling_interval = 10

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
                rtp_found = True

                rtp = data[0]

                assert rtp['payeeId'] == registry_payee_id, f"Unexpected payee ID: {rtp['payeeId']}"
                assert rtp['noticeNumber'] == common_nav, f"Unexpected notice number: {rtp['noticeNumber']}"

                break

        time.sleep(polling_interval)

    assert rtp_found, f"RTP was not created within the timeout period ({max_polling_time} seconds)"
    print('Test completed successfully: RTP was properly created with registry payee ID')
