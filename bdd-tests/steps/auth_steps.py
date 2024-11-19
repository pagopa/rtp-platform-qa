from behave import given

from api.auth import get_valid_token
from config.configuration import secrets


@given('the Service Provider is authenticated')
def given_ec_on_page(context):
    access_token = get_valid_token(client_id=secrets.client_id, client_secret=secrets.client_secret)
    context.token = access_token
