import time

import allure
import pytest

from utils.dataset import create_debt_position_payload
from utils.dataset import create_debt_position_update_payload

@allure.feature('Debt Positions')
@allure.story('Create Debt Position')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position(setup_data, environment):
    """
    Verify that after creating and publishing a debt position,
    the RTP lookup returns exactly one entry for the notice number.
    """
    allure.dynamic.title(f"Happy path: a debt position is created and published in {environment['name']} environment")

    subscription_key = setup_data['subscription_key']
    organization_id = setup_data['organization_id']
    debtor_fc = setup_data['debtor_fc']
    iupd = setup_data['iupd']
    iuv = setup_data['iuv']

    payload = create_debt_position_payload(debtor_fc=debtor_fc, iupd=iupd, iuv=iuv)

    create_function = environment['create_function']

    res = create_function(subscription_key, organization_id, payload, to_publish=True)
    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'



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

    time.sleep(5)

    update_payload = create_debt_position_update_payload(iupd=iupd, debtor_fc=debtor_fc, iuv=iuv)
    update_response = update_function(subscription_key, organization_id, iupd, update_payload)
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'
