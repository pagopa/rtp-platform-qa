import json
import random

import allure
import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.send_rtp import send_rtp
from config.configuration import config
from config.configuration import secrets
from utils.dataset import generate_rtp_data
from utils.dataset import uuidv4_pattern


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("An RTP is sent through API")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api():
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
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert (
        "/".join(location_split[:-1])
        == config.rtp_creation_base_url_path + config.send_rtp_path
    )
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider through Sender")
@allure.title("An RTP is sent to a CBI service with activated fiscal code")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.cbi
def test_send_rtp_to_cbi():
    fiscal_code = secrets.cbi_activated_fiscal_code
    payee_id = secrets.cbi_payee_id
    rtp_data = generate_rtp_data(payer_id=fiscal_code, payee_id=str(payee_id))

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )

    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert (
        "/".join(location_split[:-1])
        == config.rtp_creation_base_url_path + config.send_rtp_path
    )
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider")
@allure.title("An RTP is sent to Poste service with activated fiscal code")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.poste
def test_send_rtp_to_poste():
    amount = random.randint(100, 10000)
    rtp_data = generate_rtp_data(
        payer_id=secrets.poste_activated_fiscal_code, amount=amount
    )

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert (
        "/".join(location_split[:-1])
        == config.rtp_creation_base_url_path + config.send_rtp_path
    )
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a provider")
@allure.title("An RTP is sent to ICCREA service with activated fiscal code")
@pytest.mark.send
@pytest.mark.happy_path
@pytest.mark.real_integration
@pytest.mark.iccrea
def test_send_rtp_to_iccrea():
    rtp_data = generate_rtp_data(payer_id=secrets.iccrea_activated_fiscal_code)
    rtp_data = generate_rtp_data(
        payer_id=secrets.poste_activated_fiscal_code, amount=amount
    )

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert (
        "/".join(location_split[:-1])
        == config.rtp_creation_base_url_path + config.send_rtp_path
    )
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("Debtor fiscal code must be lower case during RTP send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_api_lower_fiscal_code():
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

    res = activate(
        debtor_service_provider_access_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert res.status_code == 201, "Error activating debtor"

    rtp_data["payer"]["payerId"] = rtp_data["payer"]["payerId"].lower()
    response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert response.status_code == 400


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("The response body contains a comprehensible error message")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_field_error_in_body():
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

    res = activate(
        debtor_service_provider_access_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert res.status_code == 201, "Error activating debtor"

    rtp_data["payee"]["payeeId"] = None
    response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert response.status_code == 400
    assert response.json()["error"] == "NotNull.createRtpDtoMono.payee.payeeId"
    assert response.json()["details"] == "payee.payeeId must not be null"


@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a non-activated debtor")
@allure.title("An RTP is sent through API")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_not_activated_user():
    rtp_data = generate_rtp_data()

    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    send_response = send_rtp(
        access_token=creditor_service_provider_access_token, rtp_payload=rtp_data
    )
    assert send_response.status_code == 422
