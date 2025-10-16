from behave import given, when
from api.auth import get_access_token, get_valid_access_token
from config.configuration import secrets


@given('the {role} Service Provider is authenticated')
def given_ec_on_page(context, role):
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
    if 'access_tokens' not in context:
        context.access_tokens = {}
    context.access_tokens[role] = access_token


@given('the {role} Service Provider is unauthenticated')
@when('the {role} Service Provider is unauthenticated')
def given_ec_on_page(context, role):
    context.access_tokens[role] = ''

@given('the {role} Service Provider B is authenticated')
def given_sp_b_authenticated(context, role):
    """Authenticate Service Provider B"""
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
    
    if not hasattr(context, 'access_tokens'):
        context.access_tokens = {}
    context.access_tokens['debtor_b'] = access_token


@given('the {role} Service Provider B is unauthenticated')
def given_sp_b_unauthenticated(context, role):
    """Set Service Provider B as unauthenticated"""
    if not hasattr(context, 'access_tokens'):
        context.access_tokens = {}
    context.access_tokens['debtor_b'] = ''
