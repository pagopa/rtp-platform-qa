from behave import then
from behave import when

from api.cancel_rtp import cancel_rtp


@when('the {role} Service send a cancellation request for the RTP')
def step_impl(context, role):
    cancel_response = cancel_rtp(context.access_tokens[role], context.latest_rtp_resource_id)
    assert cancel_response.status_code == 204, f'Error cancelling RTP, got status code: {cancel_response.status_code}'


@then('the RTP is cancelled')
def step_impl(context):
    # TODO implement this check
    assert True
