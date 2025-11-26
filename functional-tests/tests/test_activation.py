import uuid
from datetime import datetime

import allure
import pytest
import requests

from api.activation import activate
from api.activation import ACTIVATION_LIST_URL
from api.activation import get_activation_by_id
from api.activation import get_activation_by_payer_id
from api.activation import get_all_activations
from config.configuration import config
from config.configuration import secrets
from utils.dataset import fake_fc
from utils.dataset import uuidv4_pattern
from utils.random_values import random_page_size
from utils.response_assertions import is_empty_response

@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor is activated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_activate_debtor(access_token):
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
@allure.story('List Activations')
@allure.title('Get a page of activations')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_all_activations(access_token, next_cursor):
    page_size = random_page_size()
    res = get_all_activations(access_token, size=page_size)
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    body = res.json()
    assert isinstance(body.get('activations'), list), "Expected 'activations' to be a list"

    page_meta = body.get('page') or body.get('metadata')
    if page_meta is not None:
        assert isinstance(page_meta, dict), 'Expected metadata to be a dict when present'

    nid = next_cursor(res)
    if nid:
        res2 = get_all_activations(access_token, size=page_size, next_activation_id=nid)
        assert res2.status_code == 200, f'Expected 200 but got {res2.status_code}'
        body2 = res2.json()
        assert isinstance(body2.get('activations'), list), "Expected 'activations' to be a list"
        assert len(body2['activations']) <= page_size, f'Expected {page_size} or fewer activations in paginated response'


@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('A debtor is activated and retrieved by activation id')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id(access_token, make_activation):
    activation_id, debtor_fc = make_activation()

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
def test_cannot_activate_debtor_lower_fiscal_code(access_token):
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
def test_cannot_get_activation_lower_fiscal_code(access_token):
    debtor_fc = fake_fc().lower()

    res = get_activation_by_payer_id(access_token, debtor_fc)
    assert res.status_code == 400


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor service provider fails activation due to wrong service provider id')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_fail_activate_debtor_incongruent_service_provider(access_token):
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, 'WRONGS01')
    assert res.status_code == 403


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor cannot be activated more than once')
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_fail_activate_debtor_two_times(access_token):
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, f'Error activating debtor, expected 201 but got {res.status_code}'

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 409, f'Error activating debtor, expected 409 but got {res.status_code}'

    assert res.text == "" or res.text is None, "Expected empty body for 409 response on double activation"


@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving non-existent activation returns 404')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_not_found(access_token):
    random_id = str(uuid.uuid4())
    res = get_activation_by_id(access_token, random_id)
    assert res.status_code == 404


@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving activation with invalid UUID returns 400')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_invalid_uuid(access_token):
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


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Invalid pagination parameters returns 400')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
@pytest.mark.parametrize('size', [0, -5])
def test_get_all_activations_invalid_params(access_token, size):
    res = get_all_activations(access_token, size=size)
    assert res.status_code == 400, f'Expected 400 for invalid params, got {res.status_code}'
    body = res.json()
    assert isinstance(body.get('errors'), list), "Expected 'errors' list in response"
    assert body['errors'], 'Expected at least one error entry'
    assert 'code' in body['errors'][0], "Each error must have a 'code'"
    assert 'description' in body['errors'][0], "Each error must have a 'description'"


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Unauthorized request returns 401')
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_unauthorized():
    fake_token = 'Bearer invalid.token'
    res = get_all_activations(fake_token)
    assert res.status_code == 401, f'Expected 401 but got {res.status_code}'
    body = res.json()
    assert 'message' in body, "Expected 'message' in 401 response"
    assert isinstance(body['message'], str), "Expected 'message' to be a string"
    assert 'statusCode' in body, "Expected 'statusCode' in 401 response"
    assert body['statusCode'] == 401, f"Expected statusCode 401 but got {body['statusCode']}"


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Invalid NextActivationId format returns 400')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_invalid_next_activation_id_format(access_token):
    headers = {
        'Authorization': f'{access_token}',
        'Version': 'v1',
        'RequestId': str(uuid.uuid4()),
        'NextActivationId': 'not-a-valid-uuid'
    }
    res = requests.get(
        ACTIVATION_LIST_URL,
        headers=headers,
        params={'size': 5},
        timeout=config.default_timeout
    )
    assert res.status_code == 400, f'Expected 400 but got {res.status_code}'


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Non-integer size returns 400')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_non_integer_size(access_token):
    headers = {
        'Authorization': f'{access_token}',
        'Version': 'v1',
        'RequestId': str(uuid.uuid4())
    }
    res = requests.get(
        ACTIVATION_LIST_URL,
        headers=headers,
        params={'size': 'abc'},
        timeout=config.default_timeout
    )
    assert res.status_code == 400, f'Expected 400 but got {res.status_code}'


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Missing Version header returns 200')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_missing_version_header(access_token):
    headers = {
        'Authorization': f'{access_token}',
        'RequestId': str(uuid.uuid4())
    }
    res = requests.get(
        ACTIVATION_LIST_URL,
        headers=headers,
        params={'size': 5},
        timeout=config.default_timeout
    )
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'


@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Non-existent NextActivationId returns 200 with empty body')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_nonexistent_next_activation_id(access_token):
    random_cursor = str(uuid.uuid4())

    res = get_all_activations(access_token, size=5, next_activation_id=random_cursor)

    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    assert is_empty_response(res), 'Expected empty body for nonexistent NextActivationId'
