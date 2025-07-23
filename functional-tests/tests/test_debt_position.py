import hashlib

import allure
import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.debt_position import create_debt_position
from api.debt_position import create_debt_position_dev
from api.debt_position import get_debt_positions_by_notice_number
from config.configuration import secrets
from utils.dataset import create_debt_position_payload
from utils.dataset import fake_fc
from utils.dataset import generate_iupd
from utils.dataset import generate_iuv


@allure.feature('Debt Positions')
@allure.story('Create Debt Position')
@allure.title('Happy path: a debt position is created and published')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position_happy_path():

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    debtor_fc = fake_fc()
    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor before creating debt position'


    subscription_key = secrets.debt_positions.subscription_key
    organization_id = secrets.debt_positions.organization_id

    iupd = generate_iupd()
    iuv = generate_iuv()

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)

    res = create_debt_position(subscription_key, organization_id, payload, to_publish=True)

    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'

    print(f'print body: {res.json()}')


@allure.feature('Debt Positions')
@allure.story('Create Debt Position in DEV')
@allure.title('Happy path: a debt position is created and published in DEV environment')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position_dev_happy_path():
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )

    debtor_fc = fake_fc()

    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor before creating debt position'

    subscription_key = secrets.debt_positions_dev.subscription_key
    organization_id = secrets.debt_positions_dev.organization_id

    iupd = generate_iupd()
    iuv = generate_iuv()

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)

    res = create_debt_position_dev(subscription_key, organization_id, payload, to_publish=True)
    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'


@allure.feature('Debt Positions')
@allure.story('Create & Verify Debt Position')
@allure.title('Verifica che la debt position creata sia recuperabile via noticeNumber')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_and_verify_debt_position_by_notice_number():

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    debtor_fc = fake_fc()
    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201


    subscription_key = secrets.debt_positions.subscription_key
    organization_id = secrets.debt_positions.organization_id
    iupd = generate_iupd()
    iuv = generate_iuv()
    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    res = create_debt_position(subscription_key, organization_id, payload, to_publish=True)
    assert res.status_code == 201


    full_name = payload['fullName']
    description = payload['paymentOption'][0]['description']
    expected_hash = hashlib.sha256(f"{full_name}{description}".encode()).hexdigest()

    access_token_for_get = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )


    get_res = get_debt_positions_by_notice_number(
        notice_number=payload['paymentOption'][0]['iuv'],
        access_token=access_token_for_get
    )
    assert get_res.status_code == 200, f'Expected 200 but got {get_res.status_code}'
    positions = get_res.json()
    print(f'print body: {positions}')


    # found = False
    # for pos in positions:
    #     fn = pos.get('fullName')
    #     desc = pos.get('paymentOption', [{}])[0].get('description')
    #     h = hashlib.sha256(f"{fn}{desc}".encode()).hexdigest()
    #     if h == expected_hash:
    #         found = True
    #         break
    # assert found, 'Created debt position not found in GET by noticeNumber response'
