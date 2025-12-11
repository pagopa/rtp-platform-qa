from behave import given
from behave import when

from api.auth_api import get_access_token
from api.auth_api import get_valid_access_token
from config.configuration import secrets


def ensure_access_tokens_initialized(context):
    """Helper function to initialize access_tokens if not present"""
    if not hasattr(context, 'access_tokens'):
        context.access_tokens = {}


@given('the {role} Service Provider is authenticated')
def given_ec_on_page(context, role):
    ensure_access_tokens_initialized(context)

    if role == 'debtor':
        client_id = secrets.debtor_service_provider.client_id
        client_secret = secrets.debtor_service_provider.client_secret
    else:
        client_id = secrets.creditor_service_provider.client_id
        client_secret = secrets.creditor_service_provider.client_secret
    access_token = get_valid_access_token(
        client_id=client_id,
        client_secret=client_secret,
        access_token_function=get_access_token
    )
    context.access_tokens[role] = access_token


@given('the {role} Service Provider is unauthenticated')
@when('the {role} Service Provider is unauthenticated')
def given_ec_on_page(context, role):
    ensure_access_tokens_initialized(context)
    context.access_tokens[role] = ''


@given('the {role} Service Provider B is authenticated')
def given_sp_b_authenticated(context, role):
    """Authenticate Service Provider B"""
    ensure_access_tokens_initialized(context)

    if role.lower() == 'debtor':
        client_id = secrets.debtor_service_provider_B.client_id
        client_secret = secrets.debtor_service_provider_B.client_secret
    else:
        client_id = secrets.creditor_service_provider_B.client_id
        client_secret = secrets.creditor_service_provider_B.client_secret

    access_token = get_valid_access_token(
        client_id=client_id,
        client_secret=client_secret,
        access_token_function=get_access_token
    )
    context.access_tokens['debtor_b'] = access_token


@given('the {role} Service Provider B is unauthenticated')
def given_sp_b_unauthenticated(context, role):
    """Set Service Provider B as unauthenticated"""
    ensure_access_tokens_initialized(context)
    context.access_tokens['debtor_b'] = ''
