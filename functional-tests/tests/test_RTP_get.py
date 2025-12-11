import uuid

import allure
import pytest

from api.activation import activate
from api.get_rtp import get_rtp
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic('RTP Get')
@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('RTP is successfully retrieved')
@allure.tag('functional', 'happy_path', 'rtp_get')
@pytest.mark.get
@pytest.mark.happy_path
def test_get_rtp_success(debtor_service_provider_token_a, creditor_service_provider_token_a, rtp_reader_access_token):

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data['payer']['payerId'],
        secrets.debtor_service_provider.service_provider_id,
    )

    assert activation_response.status_code == 201, 'Error activating debtor'

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a, rtp_payload=rtp_data
    )

    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]

    get_response = get_rtp(
        access_token=rtp_reader_access_token, rtp_id=resource_id
    )

    assert get_response.status_code == 200
    body = get_response.json()
    assert body['resourceID'] == resource_id


@allure.epic('RTP Get')
@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('inexistent RTP -> empty body')
@allure.tag('functional', 'unhappy_path', 'rtp_get')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_not_found(rtp_reader_access_token):

    fake_rtp_id = str(uuid.uuid4())

    resp = get_rtp(access_token=rtp_reader_access_token, rtp_id=fake_rtp_id)

    assert resp.status_code in (
        404,
        204,
    ), f"Status code: {resp.status_code}, body: {resp.text}"

    if resp.status_code == 204:
        assert resp.text == ''
    else:
        assert resp.text == '' or resp.json() == {}


@allure.epic('RTP Get')
@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('malformed rtp_id → 400 Bad Request')
@allure.tag('functional', 'unhappy_path', 'rtp_get')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_invalid_id_format(creditor_service_provider_token_a):

    bad_id = '123-not-a-uuid'
    resp = get_rtp(access_token=creditor_service_provider_token_a, rtp_id=bad_id)
    assert resp.status_code == 400, f"Atteso 400, ottenuto {resp.status_code}"


@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('missing token → 401 Unauthorized')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_missing_token():

    from uuid import uuid4
    fake_rtp = str(uuid4())

    resp = get_rtp(access_token='', rtp_id=fake_rtp)
    assert resp.status_code == 401
