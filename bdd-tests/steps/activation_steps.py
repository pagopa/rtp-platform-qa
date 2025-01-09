from behave import given
from behave import then
from behave import when

from api.activation import activate
from config.configuration import secrets


@given('the {role} Service Provider activated the debtor {debtor_name}')
@when('the {role} Service Provider activates the debtor {debtor_name}')
def given_sp_activates_debtor(context, role, debtor_name):
    debtor_fc = context.debtor_fc[debtor_name]
    res = activate(context.access_tokens[role], debtor_fc, secrets.debtor_service_provider.service_provider_id)

    assert res.status_code == 201, f'Activation failed with status code {res.status_code}'


@when('the {role} Service Provider tries to activate the debtor {debtor_name}')
def given_sp_tries_to_activate_debtor(context, debtor_name, role):
    debtor_fc = context.debtor_fc[debtor_name]
    activation_response = activate(context.access_tokens[role], debtor_fc,
                                   secrets.debtor_service_provider.service_provider_id)
    context.latest_activation_response = activation_response


@then('the activation fails because the Service Provider has wrong credentials')
def then_sp_fails_activation_wrong_credentials(context):
    assert context.latest_activation_response.status_code == 401


@then('the activation fails because debtor {debtor_name} is already activated')
def then_sp_fails_activation_debtor_already_activate(context, debtor_name):
    assert context.latest_activation_response.status_code == 409
