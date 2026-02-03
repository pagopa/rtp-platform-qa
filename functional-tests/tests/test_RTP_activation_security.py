import allure

from api.debtor_activation_api import get_activation_by_id
from api.debtor_activation_api import get_activation_by_payer_id

@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Prevent unauthorized access to activations by different Service Providers')
@allure.title('SP_B cannot retrieve activation by Fiscal Code created by SP_A')
@allure.tag('security', 'activation', 'regression')
def test_sp_b_cannot_get_activation_by_fiscal_code(
    make_activation,
    debtor_service_provider_token_b
):
    _, debtor_fc = make_activation()

    response = get_activation_by_payer_id(
        access_token=debtor_service_provider_token_b,
        payer_fiscal_code=debtor_fc
    )


    if response.status_code != 404:
        print(f"SECURITY INCIDENT: SP_B found activation for {debtor_fc} created by SP_A!")
        print(f"Response Body: {response.text}")

    assert response.status_code == 404, \
        f"Expected 404 Not Found for SP_B accessing SP_A activation, but got {response.status_code}. Body: {response.text}"


@allure.epic('RTP Activation Security')
@allure.feature('Activation Security')
@allure.story('Prevent unauthorized access to activations by different Service Providers')
@allure.title('SP_B cannot retrieve activation by Activation ID created by SP_A')
@allure.tag('security', 'activation', 'regression')
def test_sp_b_cannot_get_activation_by_id(
    make_activation,
    debtor_service_provider_token_b
):

    activation_id, _ = make_activation()

    response = get_activation_by_id(
        access_token=debtor_service_provider_token_b,
        activation_id=activation_id
    )

    if response.status_code != 404:
        print(f"SECURITY INCIDENT: SP_B found activation ID {activation_id} created by SP_A!")
        print(f"Response Body: {response.text}")

    assert response.status_code == 404, \
        f"Expected 404 Not Found for SP_B accessing SP_A activation ID, but got {response.status_code}. Body: {response.text}"
