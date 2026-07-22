import uuid
from datetime import datetime

import allure
import pytest

from api.debtor_activation_api import get_activation_by_id
from config.configuration import secrets


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("A debtor is activated and retrieved by activation id")
@allure.tag("functional", "happy_path", "activation", "debtor_activation")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id(debtor_service_provider_token_a, make_activation):

    activation_id, debtor_fc = make_activation()

    res = get_activation_by_id(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    body = res.json()
    assert body["id"] == activation_id
    assert body["payer"]["fiscalCode"] == debtor_fc
    assert body["payer"]["rtpSpId"] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body["effectiveActivationDate"], "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        assert False, "Invalid date format"


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("A debtor with omocodia fiscal code is activated and retrieved by activation id")
@allure.tag("functional", "happy_path", "activation", "debtor_activation", "omocodia")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id_omocodia_fiscal_code(
    debtor_service_provider_token_a, make_activation, random_omocodia_fiscal_code
):

    activation_id, _ = make_activation(random_omocodia_fiscal_code)

    res = get_activation_by_id(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    body = res.json()
    assert body["id"] == activation_id
    assert body["payer"]["fiscalCode"] == random_omocodia_fiscal_code
    assert body["payer"]["rtpSpId"] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body["effectiveActivationDate"], "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        assert False, "Invalid date format"


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("A debtor with foreign fiscal code is activated and retrieved by activation id")
@allure.tag("functional", "happy_path", "activation", "debtor_activation", "foreign")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id_foreign_fiscal_code(
    debtor_service_provider_token_a, make_activation, random_foreign_fiscal_code
):

    activation_id, _ = make_activation(random_foreign_fiscal_code)

    res = get_activation_by_id(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    body = res.json()
    assert body["id"] == activation_id
    assert body["payer"]["fiscalCode"] == random_foreign_fiscal_code
    assert body["payer"]["rtpSpId"] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body["effectiveActivationDate"], "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        assert False, "Invalid date format"


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("A debtor with VAT number is activated and retrieved by activation id")
@allure.tag("functional", "happy_path", "activation", "debtor_activation", "vat")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_by_id_vat_number(debtor_service_provider_token_a, make_activation, random_vat_number):

    activation_id, _ = make_activation(random_vat_number)

    res = get_activation_by_id(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    body = res.json()
    assert body["id"] == activation_id
    assert body["payer"]["fiscalCode"] == random_vat_number
    assert body["payer"]["rtpSpId"] == secrets.debtor_service_provider.service_provider_id

    try:
        datetime.strptime(body["effectiveActivationDate"], "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        assert False, "Invalid date format"


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("Retrieving activation without valid token returns 401")
@allure.tag("functional", "unhappy_path", "activation", "debtor_activation")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_unauthorized():

    fake_token = "Bearer invalid.token.value"
    random_id = str(uuid.uuid4())
    res = get_activation_by_id(fake_token, random_id)
    assert res.status_code == 401


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("Retrieving non-existent activation returns 404")
@allure.tag("functional", "unhappy_path", "activation", "debtor_activation")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_not_found(debtor_service_provider_token_a):

    random_id = str(uuid.uuid4())
    res = get_activation_by_id(debtor_service_provider_token_a, random_id)
    assert res.status_code == 404
    
    error_body = res.json()
    assert "errors" in error_body
    assert isinstance(error_body["errors"], list)
    assert len(error_body["errors"]) > 0
    for err in error_body["errors"]:
        assert "code" in err
        assert "description" in err
        assert isinstance(err["code"], str)
        assert isinstance(err["description"], str)


@allure.epic("Debtor Activation")
@allure.feature("Activation")
@allure.story("Get Debtor activation by ID")
@allure.title("Retrieving activation with invalid UUID returns 400")
@allure.tag("functional", "unhappy_path", "activation", "debtor_activation")
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_by_id_invalid_uuid(debtor_service_provider_token_a):

    invalid_id = "not-a-valid-uuid"
    res = get_activation_by_id(debtor_service_provider_token_a, invalid_id)
    assert res.status_code == 400
