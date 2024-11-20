from behave import given
from behave import when

from api.activation import activate
from config.configuration import secrets


@given('the Service Provider activated the debtor {debtor_name}')
@when('the Service Provider activates the debtor {debtor_name}')
def given_ec_on_page(context, debtor_name):
    debtor_fc = context.debtor_fc[debtor_name]
    res = activate(context.access_token, debtor_fc, secrets.client_id)

    assert res.status_code == 201, 'Error activating debtor'
