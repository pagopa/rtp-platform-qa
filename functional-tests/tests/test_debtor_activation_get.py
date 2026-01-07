import uuid
from datetime import datetime

import allure
import pytest

from api.debtor_activation_api import activate
from api.debtor_activation_api import get_activation_by_id
from config.configuration import secrets
from utils.activation_helpers import activate_with_sp_a
from utils.activation_helpers import activate_with_sp_b
from utils.http_utils import extract_id_from_location


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('A debtor is activated and retrieved by activation id')
@allure.tag('functional', 'happy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id(debtor_service_provider_token_a, make_activation):

    activation_id, debtor_fc = make_activation()

    res = get_activation_by_id(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200, f'Expected 200 but got {res.status_code}'
    body = res.json()
    assert body['id'] == activation_id
    assert body['payer']['fiscalCode'] == debtor_fc
    assert body['payer']['rtpSpId'] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body['effectiveActivationDate'], '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        assert False, 'Invalid date format'

@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title(
    'A second service provider triggers takeover when debtor is already active on another service provider'
)
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation', 'takeover')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_activate_debtor_already_active_on_another_service_provider_triggers_takeover(
    debtor_service_provider_token_a, debtor_service_provider_token_b, random_fiscal_code
):

    res_a = activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code)
    assert (
        res_a.status_code == 201
    ), f"Error activating debtor, expected 201 but got {res_a.status_code} - {res_a.text}"

    res_b = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert (
        res_b.status_code == 409
    ), f"Expected 409 conflict (takeover trigger), got {res_b.status_code} - {res_b.text}"

    otp = extract_id_from_location(res_b.headers.get('Location'))
    assert (
        otp is not None
    ), 'Missing/invalid Location header (expected OTP for takeover trigger)'

@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title(
    'A debtor cannot be activated more than once by the same service provider'
)
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_fail_activate_debtor_two_times(
    debtor_service_provider_token_a, random_fiscal_code
):

    res = activate(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert (
        res.status_code == 201
    ), f"Error activating debtor, expected 201 but got {res.status_code}"

    res = activate(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert (
        res.status_code == 409
    ), f"Error activating debtor, expected 409 but got {res.status_code}"

    body = res.json()
    assert (
        isinstance(body.get('errors'), list) and body['errors']
    ), "Expected non-empty 'errors' list in 409 response"
    assert body['errors'][0].get('code') == '01031006E'
    assert body['errors'][0].get('description') == 'User is already active'



@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving activation without valid token returns 401')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_unauthorized():

    fake_token = 'Bearer invalid.token.value'
    random_id = str(uuid.uuid4())
    res = get_activation_by_id(fake_token, random_id)
    assert res.status_code == 401


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving non-existent activation returns 404')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_not_found(debtor_service_provider_token_a):

    random_id = str(uuid.uuid4())
    res = get_activation_by_id(debtor_service_provider_token_a, random_id)
    assert res.status_code == 404


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Get Debtor activation by ID')
@allure.title('Retrieving activation with invalid UUID returns 400')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_invalid_uuid(debtor_service_provider_token_a):

    invalid_id = 'not-a-valid-uuid'
    res = get_activation_by_id(debtor_service_provider_token_a, invalid_id)
    assert res.status_code == 400
