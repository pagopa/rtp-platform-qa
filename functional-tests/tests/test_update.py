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
from typing import NamedTuple, Any


TEST_TIMEOUT_SEC = 300
POLLING_RATE_SEC = 30


class UpdateCheckData(NamedTuple):
    nav: str
    description: str
    amount: int


@pytest.fixture
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
@allure.story('Update Valid  Newly Published Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_update_valid_newly_published_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position with VALID status is updated in {environment['name']} environment")

    auth_function = environment['rtp_auth_function']
    find_rtp_function = environment['find_rtp_function']

    update_data = _setup_update_test(setup_data, environment, 'VALID', to_publish=False)
    
    client_id = secrets.creditor_service_provider.client_id
    client_secret = secrets.creditor_service_provider.client_secret

    access_token = auth_function(
        client_id=client_id, 
        client_secret=client_secret)
    assert access_token is not None, f'Access token cannot be None'

    while True:
        response = find_rtp_function(access_token, update_data.nav)
        
        if response.status_code != 200:
            raise RuntimeError(f"Error calling find_rtp_by_notice_number API. Response {response.status_code}. Notice number: {update_data.nav}")
        
        data = response.json()
            
        assert not data or not type(data) is list, f'Invalid response body.'
        
        if len(data) != 1:
            rtp = data[0]
            
            assert rtp['noticeNumber'] == "expected_value", f'Wrong notice number. Expected {update_data.nav} but got {rtp['noticeNumber']}'
            assert rtp['description'] == "expected_value", f'Wrong description. Expected {update_data.description} but got {rtp['description']}'
            assert rtp['amount'] == "expected_value", f'Wrong notice number. Expected {update_data.description} but got {rtp['amount']}'
            
            break

        time.sleep(POLLING_RATE_SEC)


@allure.feature('Debt Positions')
@allure.story('Update Valid Already published Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_update_valid_already_published_debt_position(setup_data, environment):
    allure.dynamic.title(f"Happy path: a debt position with VALID status is updated in {environment['name']} environment")
    
    auth_function = environment['rtp_auth_function']
    find_rtp_function = environment['find_rtp_function']

    update_data = _setup_update_test(setup_data, environment, 'VALID')
    
    client_id = secrets.creditor_service_provider.client_id
    client_secret = secrets.creditor_service_provider.client_secret

    access_token = auth_function(
        client_id=client_id, 
        client_secret=client_secret)
    assert access_token is not None, f'Access token cannot be None'

    while True:
        response = find_rtp_function(access_token, update_data.nav)
        
        if response.status_code != 200:
            raise RuntimeError(f"Error calling find_rtp_by_notice_number API. Response {response.status_code}. Notice number: {update_data.nav}")
        
        data = response.json()
            
        assert data is not None and type(data) is list, f'Invalid response body.'
        
        if len(data) > 0:
            rtp = data[0]
            
            assert rtp['noticeNumber'] == "expected_value", f'Wrong notice number. Expected {update_data.nav} but got {rtp['noticeNumber']}'
            assert rtp['description'] == "expected_value", f'Wrong description. Expected {update_data.description} but got {rtp['description']}'
            assert rtp['amount'] == "expected_value", f'Wrong notice number. Expected {update_data.amount} but got {rtp['amount']}'
            
            break

        time.sleep(POLLING_RATE_SEC)


def _setup_update_test(
        setup_data: dict[str, Any], 
        environment: dict[str, Any], 
        status: str, to_publish: bool = True, 
        waiting_time_sec: int = 5
    ) -> UpdateCheckData:
    
    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    create_function = environment['create_function']
    update_function = environment['update_function']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)
    create_response = create_function(subscription_key, organization_id, payload, to_publish=to_publish)
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'
    
    create_response_body = create_response.json()
    expected_created_status = status if to_publish else 'DRAFT'
    assert create_response_body['status'] == expected_created_status, f'Wrong status. Expected {expected_created_status} but got {create_response_body['status']}'
    
    nav = create_response_body['paymentOption'][0]['nav']
    assert nav is not None, f'NAV cannot be None'
    
    description = create_response_body['paymentOption'][0]['description']
    amount = create_response_body['paymentOption'][0]['amount']

    time.sleep(waiting_time_sec)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_function(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'
    
    update_response_body = update_response.json()
    assert update_response_body['status'] == status, f'Wrong status. Expected {status} but got {update_response_body['status']}'
    
    return UpdateCheckData(nav, description, amount)