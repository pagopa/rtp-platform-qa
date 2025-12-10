import uuid

import allure
import pytest

from api.cancel_rtp import cancel_rtp
from api.send_rtp import send_rtp
from utils.dataset import generate_rtp_data

@allure.epic('RTP Cancel')
@allure.feature('RTP Cancel')
@allure.story('Service provider cancels RTP')
@allure.title('RTP is successfully cancelled')
@allure.tag('functional', 'happy_path', 'rtp_cancel')
@pytest.mark.cancel
@pytest.mark.happy_path
def test_cancel_rtp_success(creditor_service_provider_token_a, activate_payer):

    rtp_data = generate_rtp_data()
    creditor_service_provider_access_token = creditor_service_provider_token_a

    activation_response = activate_payer(rtp_data['payer']['payerId'])

    assert activation_response.status_code == 201, 'Error activating debtor'

    send_response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]

    cancel_response = cancel_rtp(creditor_service_provider_access_token, resource_id)
    assert cancel_response.status_code == 204


@allure.epic('RTP Cancel')
@allure.feature('RTP Cancel')
@allure.story('Service provider cancels RTP')
@allure.title('RTP cancellation fails if ID does not exist')
@allure.tag('functional', 'unhappy_path', 'rtp_cancel')
@pytest.mark.cancel
@pytest.mark.unhappy_path
def test_cancel_rtp_with_nonexistent_resource_id(creditor_service_provider_token_a):

    creditor_service_provider_access_token = creditor_service_provider_token_a
    fake_resource_id = str(uuid.uuid4())
    cancel_response = cancel_rtp(creditor_service_provider_access_token, fake_resource_id)
    assert cancel_response.status_code == 404, 'Expected 404 Not Found for non-existent resource'
