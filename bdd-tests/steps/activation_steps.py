from behave import given
from behave import then
from behave import when

from api.activation import activate
from config.configuration import secrets


@given('the Service Provider activated the debtor {debtor_name}')
@when('the Service Provider activates the debtor {debtor_name}')
def given_sp_activates_debtor(context, debtor_name):
    debtor_fc = context.debtor_fc[debtor_name]
    res = activate(context.access_token, debtor_fc, secrets.service_provider_id)
    assert res.status_code == 201


@when('the Service Provider tries to activate the debtor {debtor_name}')
def given_sp_tries_to_activate_debtor(context, debtor_name):
    debtor_fc = context.debtor_fc[debtor_name]
    activation_response = activate(context.access_token, debtor_fc, secrets.service_provider_id)
    context.activation_response = activation_response


@then('the activation fails because the Service Provider has wrong credentials')
def then_sp_fails_activation_wrong_credentials(context):
    assert context.activation_response == 403


@then('the activation fails because debtor {debtor_name} is already activated')
def then_sp_fails_activation_debtor_already_activate(context, debtor_name):
    assert context.activation_response == 409
