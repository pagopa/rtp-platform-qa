from datetime import datetime

import allure
import pytest

from api.debtor_activation_api import activate
from api.debtor_activation_api import get_activation_by_payer_id
from config.configuration import config
from config.configuration import secrets
from utils.activation_helpers import activate_with_sp_a
from utils.activation_helpers import activate_with_sp_b
from utils.http_utils import extract_id_from_location
from utils.regex_utils import uuidv4_pattern


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor is activated by an authenticated service provider')
@allure.tag('functional', 'happy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_activate_debtor(debtor_service_provider_token_a, random_fiscal_code):

    res = activate(debtor_service_provider_token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    location = res.headers['Location']
    location_split = location.split('/')

    assert '/'.join(location_split[:-1]) == config.activation_base_url_path + config.activation_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))

    res = get_activation_by_payer_id(debtor_service_provider_token_a, random_fiscal_code)
    assert res.status_code == 200
    assert res.json()['payer']['fiscalCode'] == random_fiscal_code
    assert res.json()['payer']['rtpSpId'] == secrets.debtor_service_provider.service_provider_id
    assert bool(uuidv4_pattern.fullmatch(res.json()['id']))

    try:
        datetime.strptime(res.json()['effectiveActivationDate'], '%Y-%m-%dT%H:%M:%S.%f')
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
    assert body['errors'][0]['code'] == '01031006E'
    assert body['errors'][0]['description'] == 'User is already active'

@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('The activation request must contain lower case fiscal code')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_cannot_activate_debtor_lower_fiscal_code(debtor_service_provider_token_a, random_fiscal_code):

    res = activate(debtor_service_provider_token_a, random_fiscal_code.lower(), secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 400
    assert res.json()['errors'][0]['code'] == 'Pattern.activationReqDtoMono.payer.fiscalCode'
    assert res.json()['errors'][0]['description'].startswith('payer.fiscalCode must match')


@allure.epic('Debtor Activation')
@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('Find by payer id request must contain lower case fiscal code')
@allure.tag('functional', 'unhappy_path', 'activation', 'debtor_activation')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_cannot_get_activation_lower_fiscal_code(debtor_service_provider_token_a, random_fiscal_code):

    res = get_activation_by_payer_id(debtor_service_provider_token_a, random_fiscal_code.lower())
    assert res.status_code == 400
