import allure
import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.get_rtp import get_rtp
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset import generate_rtp_data


@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('RTP is successfully retrieved')
@pytest.mark.get
@pytest.mark.happy_path
def test_get_rtp_success():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    activation_response = activate(
        debtor_service_provider_access_token,
        rtp_data['payer']['payerId'],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, 'Error activating debtor'

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers['Location']
    resource_id = location.split('/')[-1]

    get_response = get_rtp(
        access_token=creditor_service_provider_access_token, rtp_id=resource_id
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body['resourceID'] == resource_id


import uuid
import pytest
import allure

from api.auth import get_access_token, get_valid_access_token
from api.get_rtp import get_rtp
from config.configuration import secrets


@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('inexistent RTP -> empty body')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_not_found():
    fake_rtp_id = str(uuid.uuid4())

    token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    resp = get_rtp(access_token=token, rtp_id=fake_rtp_id)

    assert resp.status_code in (
        404,
        204,
    ), f"Status code: {resp.status_code}, body: {resp.text}"

    if resp.status_code == 204:
        assert resp.text == ''
    else:
        assert resp.text == '' or resp.json() == {}


import pytest
import allure
from api.auth import get_access_token, get_valid_access_token
from api.get_rtp import get_rtp
from config.configuration import secrets


@allure.feature('RTP Get')
@allure.story('Service provider retrieves an RTP')
@allure.title('malformed rtp_id → 400 Bad Request')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_invalid_id_format():
    bad_id = '123-not-a-uuid'
    token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    resp = get_rtp(access_token=token, rtp_id=bad_id)
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
