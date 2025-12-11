import uuid

import allure
import pytest
import requests

from api.debtor_activation_api import activate
from api.debtor_activation_api import ACTIVATION_LIST_URL
from api.debtor_activation_api import get_all_activations
from config.configuration import config
from config.configuration import secrets
from utils.random_values import random_page_size
from utils.response_assertions import is_empty_response

@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Get a page of activations')
@allure.tag('functional', 'happy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_all_activations(debtor_service_provider_token_a, next_cursor):

    page_size = random_page_size()
    res = get_all_activations(debtor_service_provider_token_a, size=page_size)
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    body = res.json()
    assert isinstance(body.get('activations'), list), "Expected 'activations' to be a list"

    page_meta = body.get('page') or body.get('metadata')
    if page_meta is not None:
        assert isinstance(page_meta, dict), 'Expected metadata to be a dict when present'

    nid = next_cursor(res)
    if nid:
        res2 = get_all_activations(debtor_service_provider_token_a, size=page_size, next_activation_id=nid)
        assert res2.status_code == 200, f'Expected 200 but got {res2.status_code}'
        body2 = res2.json()
        assert isinstance(body2.get('activations'), list), "Expected 'activations' to be a list"
        assert len(body2['activations']) <= page_size, f'Expected {page_size} or fewer activations in paginated response'



@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor service provider fails activation due to wrong service provider id')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_fail_activate_debtor_incongruent_service_provider(debtor_service_provider_token_a, random_fiscal_code):

    res = activate(debtor_service_provider_token_a, random_fiscal_code, 'WRONGS01')
    assert res.status_code == 403


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor cannot be activated more than once')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_fail_activate_debtor_two_times(debtor_service_provider_token_a, random_fiscal_code):

    res = activate(debtor_service_provider_token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, f'Error activating debtor, expected 201 but got {res.status_code}'

    res = activate(debtor_service_provider_token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 409, f'Error activating debtor, expected 409 but got {res.status_code}'

    assert res.text == '' or res.text is None, 'Expected empty body for 409 response on double activation'


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Invalid pagination parameters returns 400')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
@pytest.mark.parametrize('size', [0, -5])
def test_get_all_activations_invalid_params(debtor_service_provider_token_a, size):

    res = get_all_activations(debtor_service_provider_token_a, size=size)
    assert res.status_code == 400, f'Expected 400 for invalid params, got {res.status_code}'
    body = res.json()
    assert isinstance(body.get('errors'), list), "Expected 'errors' list in response"
    assert body['errors'], 'Expected at least one error entry'
    assert 'code' in body['errors'][0], "Each error must have a 'code'"
    assert 'description' in body['errors'][0], "Each error must have a 'description'"


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Unauthorized request returns 401')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
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


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Invalid NextActivationId format returns 400')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_invalid_next_activation_id_format(debtor_service_provider_token_a):

    headers = {
        'Authorization': f'{debtor_service_provider_token_a}',
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


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Non-integer size returns 400')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_non_integer_size(debtor_service_provider_token_a):

    headers = {
        'Authorization': f'{debtor_service_provider_token_a}',
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


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Missing Version header returns 200')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_missing_version_header(debtor_service_provider_token_a):

    headers = {
        'Authorization': f'{debtor_service_provider_token_a}',
        'RequestId': str(uuid.uuid4())
    }
    res = requests.get(
        ACTIVATION_LIST_URL,
        headers=headers,
        params={'size': 5},
        timeout=config.default_timeout
    )
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('List Activations')
@allure.title('Non-existent NextActivationId returns 200 with empty body')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_all_activations_nonexistent_next_activation_id(debtor_service_provider_token_a):

    random_cursor = str(uuid.uuid4())

    res = get_all_activations(debtor_service_provider_token_a, size=5, next_activation_id=random_cursor)

    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    assert is_empty_response(res), 'Expected empty body for nonexistent NextActivationId'
