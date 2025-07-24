import time

import allure
import pytest

from api.activation import activate
from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.debt_position import create_debt_position
from api.debt_position import create_debt_position_dev
from api.debt_position import delete_debt_position
from api.debt_position import delete_debt_position_dev
from api.debt_position import get_debt_position
from api.debt_position import get_debt_position_dev
from api.debt_position import update_debt_position
from api.debt_position import update_debt_position_dev
from config.configuration import secrets
from utils.dataset import create_debt_position_payload
from utils.dataset import create_debt_position_update_payload
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

    get_response = get_debt_position(subscription_key, organization_id, iupd)
    assert get_response.status_code == 200, f'Expected 200 but got {get_response.status_code}'

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

    get_response = get_debt_position_dev(subscription_key, organization_id, iupd)
    assert get_response.status_code == 200, f'Expected 200 but got {get_response.status_code}'

@allure.feature('Debt Positions')
@allure.story('Delete Debt Position')
@allure.title('Happy path: a debt position is deleted')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_delete_debt_position_happy_path():
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

    create_response = create_debt_position(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    import time
    time.sleep(1)

    delete_response = delete_debt_position(subscription_key, organization_id, iupd)
    assert delete_response.status_code == 200, f'Expected 200 but got {delete_response.status_code}'

    get_response = get_debt_position(subscription_key, organization_id, iupd)
    assert get_response.status_code == 404, f'Expected 404 but got {get_response.status_code}'

@allure.feature('Debt Positions')
@allure.story('Delete Debt Position')
@allure.title('Happy path: a debt position is deleted')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_delete_debt_position_dev_happy_path():
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

    create_response = create_debt_position_dev(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    import time
    time.sleep(1)

    delete_response = delete_debt_position_dev(subscription_key, organization_id, iupd)
    assert delete_response.status_code == 200, f'Expected 200 but got {delete_response.status_code}'

    get_response = get_debt_position(subscription_key, organization_id, iupd)
    assert get_response.status_code == 404, f'Expected 404 but got {get_response.status_code}'


@allure.feature('Debt Positions')
@allure.story('Update Debt Position')
@allure.title('Happy path: a debt position is updated')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_update_debt_position_happy_path():
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

    create_response = create_debt_position(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    get_initial_response = get_debt_position(subscription_key, organization_id, iupd)
    assert get_initial_response.status_code == 200, f'Expected 200 but got {get_initial_response.status_code}'
    initial_data = get_initial_response.json()
    initial_description = initial_data['paymentOption'][0]['description']
    initial_amount = initial_data['paymentOption'][0]['amount']

    time.sleep(1)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_debt_position(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'

    get_updated_response = get_debt_position(subscription_key, organization_id, iupd)
    assert get_updated_response.status_code == 200, f'Expected 200 but got {get_updated_response.status_code}'
    updated_data = get_updated_response.json()
    updated_description = updated_data['paymentOption'][0]['description']
    updated_amount = updated_data['paymentOption'][0]['amount']

    assert initial_description != updated_description, 'Description was not updated'
    assert initial_amount != updated_amount, 'Amount was not updated'
    assert updated_description == 'Canone Unico Patrimoniale - CORPORATE Updated', "Description doesn't match expected value"
    assert updated_amount == 9500, "Amount doesn't match expected value"


@allure.feature('Debt Positions')
@allure.story('Update Debt Position in DEV')
@allure.title('Happy path: a debt position is updated in DEV environment')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_update_debt_position_dev_happy_path():
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

    create_response = create_debt_position_dev(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    get_initial_response = get_debt_position_dev(subscription_key, organization_id, iupd)
    assert get_initial_response.status_code == 200, f'Expected 200 but got {get_initial_response.status_code}'
    initial_data = get_initial_response.json()
    initial_description = initial_data['paymentOption'][0]['description']
    initial_amount = initial_data['paymentOption'][0]['amount']

    time.sleep(1)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_debt_position_dev(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'

    get_updated_response = get_debt_position_dev(subscription_key, organization_id, iupd)
    assert get_updated_response.status_code == 200, f'Expected 200 but got {get_updated_response.status_code}'
    updated_data = get_updated_response.json()
    updated_description = updated_data['paymentOption'][0]['description']
    updated_amount = updated_data['paymentOption'][0]['amount']

    assert initial_description != updated_description, 'Description was not updated'
    assert initial_amount != updated_amount, 'Amount was not updated'
    assert updated_description == 'Canone Unico Patrimoniale - CORPORATE Updated', "Description doesn't match expected value"
    assert updated_amount == 9500, "Amount doesn't match expected value"
