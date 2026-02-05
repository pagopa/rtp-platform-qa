import allure
import pytest

from api.debtor_activation_api import get_activation_by_id
from api.debtor_activation_api import get_activation_by_payer_id

@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Prevent unauthorized access to activations by different Service Providers')
@allure.title('SP_B cannot retrieve activation by Fiscal Code created by SP_A')
@allure.tag('security', 'activation', 'regression', 'unhappy_path')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_sp_b_cannot_get_activation_by_fiscal_code(
    make_activation,
    debtor_service_provider_token_b
):
    _, debtor_fc = make_activation()

    response = get_activation_by_payer_id(
        access_token=debtor_service_provider_token_b,
        payer_fiscal_code=debtor_fc
    )
    assert response.status_code == 404, \
        f"Expected 404 Not Found for SP_B accessing SP_A activation, but got {response.status_code}. Body: {response.text}"


@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Prevent unauthorized access to activations by different Service Providers')
@allure.title('SP_B cannot retrieve activation by Activation ID created by SP_A')
@allure.tag('security', 'activation', 'regression', 'unhappy_path')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_sp_b_cannot_get_activation_by_id(
    make_activation,
    debtor_service_provider_token_b
):

    activation_id, _ = make_activation()

    response = get_activation_by_id(
        access_token=debtor_service_provider_token_b,
        activation_id=activation_id
    )
    assert response.status_code == 404, \
        f"Expected 404 Not Found for SP_B accessing SP_A activation ID, but got {response.status_code}. Body: {response.text}"


@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Admin role can read activations across all Service Providers')
@allure.title('SP_ACTIVATIONS_READ_ALL can retrieve activation by Fiscal Code created by SP_A')
@allure.tag('security', 'activation', 'regression', 'happy_path')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_read_all_can_get_activation_by_fiscal_code(
    make_activation,
    sp_activations_read_all_token
):
    _, debtor_fc = make_activation()

    response = get_activation_by_payer_id(
        access_token=sp_activations_read_all_token,
        payer_fiscal_code=debtor_fc
    )
    assert response.status_code == 200, \
        f"Expected 200 OK for SP_ACTIVATIONS_READ_ALL accessing SP_A activation, but got {response.status_code}. Body: {response.text}"


@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Admin role can read activations across all Service Providers')
@allure.title('SP_ACTIVATIONS_READ_ALL can retrieve activation by Activation ID created by SP_A')
@allure.tag('security', 'activation', 'regression', 'happy_path')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_read_all_can_get_activation_by_id(
    make_activation,
    sp_activations_read_all_token
):
    activation_id, _ = make_activation()

    response = get_activation_by_id(
        access_token=sp_activations_read_all_token,
        activation_id=activation_id
    )
    assert response.status_code == 200, \
        f"Expected 200 OK for SP_ACTIVATIONS_READ_ALL accessing SP_A activation ID, but got {response.status_code}. Body: {response.text}"
