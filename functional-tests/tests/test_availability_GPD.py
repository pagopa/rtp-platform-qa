import time

import allure
import pytest

from utils.dataset import create_debt_position_payload
from utils.dataset import create_debt_position_update_payload

@allure.epic('GPD Availability')
@allure.feature('Create Debt Positions happy path')
@allure.story('Create Debt Position')
@allure.tag('debt_positions', 'happy_path', 'availability')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position(gpd_test_data, environment):
    """
        Verify that a debt position can be created and published successfully.
    """
    allure.dynamic.title(f"Happy path: a debt position is created and published in {environment['name']} environment")

    payload = create_debt_position_payload(
        debtor_fc=gpd_test_data.debtor_fc,
        iupd=gpd_test_data.iupd,
        iuv=gpd_test_data.iuv
    )

    res = environment['create_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        payload,
        to_publish=True
    )
    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'


@allure.epic('GPD Availability')
@allure.feature('Delete Debt Positions happy path')
@allure.story('Delete Debt Position')
@allure.tag('debt_positions', 'happy_path, availability')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_delete_debt_position(gpd_test_data, environment):
    """
        Verify that a debt position can be deleted successfully.
    """
    allure.dynamic.title(f"Happy path: a debt position is deleted in {environment['name']} environment")

    payload = create_debt_position_payload(
        debtor_fc=gpd_test_data.debtor_fc,
        iupd=gpd_test_data.iupd,
        iuv=gpd_test_data.iuv
    )

    create_response = environment['create_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        payload,
        to_publish=True
    )
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    time.sleep(1)

    delete_response = environment['delete_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        gpd_test_data.iupd
    )
    assert delete_response.status_code == 200, f'Expected 200 but got {delete_response.status_code}'

    get_response = environment['get_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        gpd_test_data.iupd
    )
    assert get_response.status_code == 404, f'Expected 404 but got {get_response.status_code}'


@allure.epic('GPD Availability')
@allure.feature('Update Debt Positions happy path')
@allure.story('Update Debt Position')
@allure.tag('debt_positions', 'happy_path, availability')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_update_debt_position(gpd_test_data, environment):
    """
        Verify that a debt position can be updated successfully.
    """
    allure.dynamic.title(f"Happy path: a debt position is updated in {environment['name']} environment")

    payload = create_debt_position_payload(
        debtor_fc=gpd_test_data.debtor_fc,
        iupd=gpd_test_data.iupd,
        iuv=gpd_test_data.iuv
    )

    create_response = environment['create_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        payload,
        to_publish=True
    )
    assert create_response.status_code == 201, f'Expected 201 but got {create_response.status_code}'

    get_initial_response = environment['get_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        gpd_test_data.iupd
    )
    assert get_initial_response.status_code == 200, f'Expected 200 but got {get_initial_response.status_code}'

    time.sleep(5)

    update_payload = create_debt_position_update_payload(
        iupd=gpd_test_data.iupd,
        debtor_fc=gpd_test_data.debtor_fc,
        iuv=gpd_test_data.iuv
    )

    update_response = environment['update_function'](
        gpd_test_data.subscription_key,
        gpd_test_data.organization_id,
        gpd_test_data.iupd,
        update_payload
    )
    assert update_response.status_code == 200, f'Expected 200 but got {update_response.status_code}'
