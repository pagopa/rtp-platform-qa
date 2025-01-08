from behave import given
from behave import when

from api.auth import get_valid_access_token
from config.configuration import secrets


@given('the Service Provider is authenticated')
def given_ec_on_page(context):
    access_token = get_valid_access_token(client_id=secrets.client_id, client_secret=secrets.client_secret)
    context.access_token = access_token


@given('the Service Provider is unauthenticated')
@when('the Service Provider is unauthenticated')
def given_ec_on_page(context):
    context.access_token = ''
