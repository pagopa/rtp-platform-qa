import time

import allure
import pytest

from api.activation import activate
from api.activation import activate_dev
from api.auth import get_access_token
from api.auth import get_access_token_dev
from api.auth import get_valid_access_token
from api.debt_position import create_debt_position
from api.debt_position import delete_debt_position
from api.debt_position import get_debt_position
from api.debt_position import update_debt_position
from api.get_rtp import get_rtp_by_notice_number
from config.configuration import secrets
from utils.dataset import create_debt_position_payload
from utils.dataset import create_debt_position_update_payload
from utils.dataset import fake_fc
from utils.dataset import generate_iupd
from utils.dataset import generate_iuv


TEST_TIMEOUT_SEC = 300
POLLING_RATE_SEC = 10


@pytest.fixture(
    params=[
        {'name': 'UAT', 'is_dev': False},
        {'name': 'DEV', 'is_dev': True}
    ],
    ids=['environment_uat', 'environment_dev']
)
def environment(request):
    """Fixture to provide environment-specific configurations."""
    env = request.param
    is_dev = env['is_dev']
    
    env.update({
        'create_function': lambda sk, org_id, payload, to_publish: create_debt_position(sk, org_id, payload, to_publish, is_dev),
        'get_function': lambda sk, org_id, iupd: get_debt_position(sk, org_id, iupd, is_dev),
        'delete_function': lambda sk, org_id, iupd: delete_debt_position(sk, org_id, iupd, is_dev),
        'update_function': lambda sk, org_id, iupd, payload, to_publish=True: update_debt_position(sk, org_id, iupd, payload, to_publish, is_dev),
        'rtp_auth_function': lambda client_id, client_secret, access_token_function=get_access_token: get_valid_access_token(client_id, client_secret, access_token_function),
        'find_rtp_function': get_rtp_by_notice_number,
        'subscription_key': secrets.debt_positions_dev.subscription_key if is_dev else secrets.debt_positions.subscription_key,
        'organization_id': secrets.debt_positions_dev.organization_id if is_dev else secrets.debt_positions.organization_id
    })

    return env


@pytest.fixture
def setup_data(environment):
    access_token_function = get_access_token_dev if environment['is_dev'] else get_access_token

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=access_token_function
    )

    debtor_fc = fake_fc()

    activation_function = activate_dev if environment['is_dev'] else activate

    activation_response = activation_function(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor before creating debt position'

    iupd = generate_iupd()
    iuv = generate_iuv()

    return {
        'debtor_fc': debtor_fc,
        'iupd': iupd,
        'iuv': iuv,
        'subscription_key': environment['subscription_key'],
        'organization_id': environment['organization_id'],
    }


@allure.feature('Debt Positions')
@allure.story('Create Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position is created and published in {environment['name']} environment")

    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)

    create_function = environment['create_function']
    get_function = environment['get_function']

    res = create_function(subscription_key, organization_id, payload, to_publish=True)
    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'

    get_response = get_function(subscription_key, organization_id, iupd)
    assert get_response.status_code == 200, f'Expected 200 but got {get_response.status_code}'


@allure.feature('Debt Positions')
@allure.story('Delete Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_delete_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position is deleted in {environment['name']} environment")

    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    create_function = environment['create_function']
    delete_function = environment['delete_function']
    get_function = environment['get_function']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    create_response = create_function(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    time.sleep(1)

    delete_response = delete_function(subscription_key, organization_id, iupd)
    assert delete_response.status_code == 200, f'Expected 200 but got {delete_response.status_code}'

    get_response = get_function(subscription_key, organization_id, iupd)
    assert get_response.status_code == 404, f'Expected 404 but got {get_response.status_code}'


@allure.feature('Debt Positions')
@allure.story('Update Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_update_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position is updated in {environment['name']} environment")

    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    create_function = environment['create_function']
    update_function = environment['update_function']
    get_function = environment['get_function']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    create_response = create_function(subscription_key, organization_id, payload, to_publish=True)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    get_initial_response = get_function(subscription_key, organization_id, iupd)
    assert get_initial_response.status_code == 200, f'Expected 200 but got {get_initial_response.status_code}'
    initial_data = get_initial_response.json()
    initial_description = initial_data['paymentOption'][0]['description']
    initial_amount = initial_data['paymentOption'][0]['amount']

    time.sleep(5)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_function(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'

    get_updated_response = get_function(subscription_key, organization_id, iupd)
    assert get_updated_response.status_code == 200, f'Expected 200 but got {get_updated_response.status_code}'
    updated_data = get_updated_response.json()
    updated_description = updated_data['paymentOption'][0]['description']
    updated_amount = updated_data['paymentOption'][0]['amount']

    assert initial_description != updated_description, 'Description was not updated'
    assert initial_amount != updated_amount, 'Amount was not updated'
    assert updated_description == 'Canone Unico Patrimoniale - CORPORATE Updated', "Description doesn't match expected value"
    assert updated_amount == 9500, "Amount doesn't match expected value"


@allure.feature('Debt Positions')
@allure.story('Update Valid Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_update_valid_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position with VALID status is updated in {environment['name']} environment")

    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    create_function = environment['create_function']
    update_function = environment['update_function']
    auth_function = environment['rtp_auth_function']
    find_rtp_function = environment['find_rtp_function']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    create_response = create_function(subscription_key, organization_id, payload, to_publish=False)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'
    
    create_response_body = create_response.json()
    expected_created_status = 'DRAFT'
    assert create_response_body['status'] == expected_created_status, f'Wrong status. Expected {expected_created_status} but got {create_response_body['status']}'
    
    nav = create_response_body['paymentOption'][0]['nav']
    assert nav is not None, f'NAV cannot be None'
    
    description = create_response_body['paymentOption'][0]['description']
    amount = create_response_body['paymentOption'][0]['amount']

    time.sleep(5)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_function(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'
    
    update_response_body = update_response.json()
    expected_update_status = 'VALID'
    assert update_response_body['status'] == expected_update_status, f'Wrong status. Expected {expected_update_status} but got {update_response_body['status']}'
    
    client_id = secrets.creditor_service_provider.client_id
    client_secret = secrets.creditor_service_provider.client_secret

    access_token = auth_function(
        client_id=client_id, 
        client_secret=client_secret)
    assert access_token is not None, f'Access token cannot be None'

    while True:
        response = find_rtp_function(access_token, nav)
        
        try:
            assert response.status_code == 200, f'Expected 200 but got {response.status_code}'
            
            data = response.json()
            assert not data or not type(data) is list or len(data) != 1, f'Invalid response body.'
            
            assert data['noticeNumber'] == "expected_value", f'Wrong notice number. Expected {nav} but got {data['noticeNumber']}'
            assert data['description'] == "expected_value", f'Wrong description. Expected {description} but got {data['description']}'
            assert data['amount'] == "expected_value", f'Wrong notice number. Expected {amount} but got {data['amount']}'
            
            break
        
        except AssertionError as e:
            print(f'---> {str(e)}')
            pass

        time.sleep(POLLING_RATE_SEC)
