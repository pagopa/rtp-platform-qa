from behave import given, when, then
from api.activation import activate, get_activation_by_payer_id
from api.takeover import takeover_activation
from config.configuration import secrets


@when('the {role} Service Provider B attempts to activate the debtor {debtor_name}')
def when_sp_b_attempts_activation(context, role, debtor_name):
    """Attempt activation with Service Provider B to trigger conflict and get OTP"""
    debtor_fc = context.debtor_fc[debtor_name]
    
    activation_response = activate(
        context.access_tokens['debtor_b'], 
        debtor_fc,
        secrets.debtor_service_provider_B.service_provider_id
    )
    
    context.latest_activation_response = activation_response
    
    if activation_response.status_code == 409:
        location_header = activation_response.headers.get('Location')
        if location_header:
            context.otp = location_header.split('/')[-1]


@when('the {role} Service Provider B performs takeover for debtor {debtor_name}')
def when_sp_b_performs_takeover(context, role, debtor_name):
    """Perform the actual takeover using the OTP"""
    debtor_fc = context.debtor_fc[debtor_name]
    
    takeover_response = takeover_activation(
        context.access_tokens['debtor_b'],
        debtor_fc,
        secrets.debtor_service_provider_B.service_provider_id,
        context.otp
    )
    
    context.latest_takeover_response = takeover_response


@when('the {role} Service Provider B tries takeover with invalid OTP for debtor {debtor_name}')
def when_sp_b_attempts_with_invalid_otp(context, role, debtor_name):
    """Attempt takeover with invalid OTP"""
    debtor_fc = context.debtor_fc[debtor_name]
    
    invalid_otp = "invalid-otp-12345"
    
    takeover_response = takeover_activation(
        context.access_tokens['debtor_b'],
        debtor_fc,
        secrets.debtor_service_provider_B.service_provider_id,
        invalid_otp
    )
    
    context.latest_takeover_response = takeover_response


@when('the unauthenticated {role} Service Provider B attempts takeover for debtor {debtor_name}')
def when_sp_b_attempts_takeover_unauth(context, role, debtor_name):
    """Attempt takeover without proper authentication"""
    debtor_fc = context.debtor_fc[debtor_name]
    
    takeover_response = takeover_activation(
        context.access_tokens.get('debtor_b', ''),
        debtor_fc,
        secrets.debtor_service_provider_B.service_provider_id,
        "any-otp"
    )
    
    context.latest_takeover_response = takeover_response


@then('the debtor {debtor_name} is now managed by Service Provider B')
def then_debtor_managed_by_sp_b(context, debtor_name):
    """Verify the debtor is now activated with Service Provider B"""
    assert context.latest_takeover_response.status_code == 201, \
        f"Takeover failed with status {context.latest_takeover_response.status_code}"
    
    debtor_fc = context.debtor_fc[debtor_name]
    
    get_response = get_activation_by_payer_id(context.access_tokens['debtor_b'], debtor_fc)
    assert get_response.status_code == 200
    assert get_response.json()['payer']['fiscalCode'] == debtor_fc
    assert get_response.json()['payer']['rtpSpId'] == secrets.debtor_service_provider_B.service_provider_id


@then('the takeover fails because of invalid OTP')
def then_takeover_fails_invalid_otp(context):
    """Verify takeover fails due to invalid OTP"""
    assert context.latest_takeover_response.status_code in [400, 401], \
        f"Expected 400/401 for invalid OTP, got {context.latest_takeover_response.status_code}"


@then('the takeover fails because the Service Provider has wrong credentials')
def then_takeover_fails_wrong_credentials(context):
    """Verify takeover fails due to authentication issues"""
    assert context.latest_takeover_response.status_code == 401, \
        f"Expected 401 for wrong credentials, got {context.latest_takeover_response.status_code}"