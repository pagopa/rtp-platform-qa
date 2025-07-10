import uuid
from datetime import datetime

import allure
import pytest

from api.activation import activate
from api.activation import get_activation_by_id
from api.activation import get_activation_by_payer_id
from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets
from utils.dataset import fake_fc
from utils.dataset import uuidv4_pattern


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor is activated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_activate_debtor():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret,
                                          access_token_function=get_access_token)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    location = res.headers['Location']
    location_split = location.split('/')

    assert '/'.join(location_split[:-1]) == config.activation_base_url_path + config.activation_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))

    res = get_activation_by_payer_id(access_token, debtor_fc)
    assert res.status_code == 200
    assert res.json()['payer']['fiscalCode'] == debtor_fc
    assert res.json()['payer']['rtpSpId'] == secrets.debtor_service_provider.service_provider_id
    assert bool(uuidv4_pattern.fullmatch(res.json()['id']))

    try:
        datetime.strptime(res.json()['effectiveActivationDate'], '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        assert False, 'Invalid date format'


@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('A debtor is activated and retrieved by activation id')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    location = res.headers['Location']
    activation_id = location.split('/')[-1]
    assert bool(uuidv4_pattern.fullmatch(activation_id))

    res = get_activation_by_id(access_token, activation_id)
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    body = res.json()
    assert body['id'] == activation_id
    assert body['payer']['fiscalCode'] == debtor_fc
    assert body['payer']['rtpSpId'] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body['effectiveActivationDate'], '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        assert False, 'Invalid date format'


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('The activation request must contain lower case fiscal code')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_cannot_activate_debtor_lower_fiscal_code():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret,
                                          access_token_function=get_access_token)
    debtor_fc = fake_fc().lower()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 400
    assert res.json()['errors'][0]['code'] == 'Pattern.activationReqDtoMono.payer.fiscalCode'
    assert res.json()['errors'][0]['description'].startswith('payer.fiscalCode must match')


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('Find by payer id request must contain lower case fiscal code')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_cannot_get_activation_lower_fiscal_code():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret,
                                          access_token_function=get_access_token)
    debtor_fc = fake_fc().lower()

    res = get_activation_by_payer_id(access_token, debtor_fc)
    assert res.status_code == 400

@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor service provider fails activation due to wrong service provider id')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_fail_activate_debtor_incongruent_service_provider():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret,
                                          access_token_function=get_access_token)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, 'WRONGS01')
    assert res.status_code == 403


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor cannot be activated more than once')
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_fail_activate_debtor_two_times():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret,
                                          access_token_function=get_access_token)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, f'Error activating debtor, expected 201 but got {res.status_code}'

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 409, f'Error activating debtor, expected 409 but got {res.status_code}'
    assert res.json()['errors'][0]['code'] == '01031000E'

@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving non-existent activation returns 404')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_not_found():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    random_id = str(uuid.uuid4())
    res = get_activation_by_id(access_token, random_id)
    assert res.status_code == 404

@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving activation with invalid UUID returns 400')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_invalid_uuid():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    invalid_id = 'not-a-valid-uuid'
    res = get_activation_by_id(access_token, invalid_id)
    assert res.status_code == 400

@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving activation without valid token returns 401')
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_unauthorized():
    fake_token = 'Bearer invalid.token.value'
    random_id = str(uuid.uuid4())
    res = get_activation_by_id(fake_token, random_id)
    assert res.status_code == 401
