import uuid

from behave import given
from behave import then
from behave import when

from api.RTP_cancel_api import cancel_rtp


@when('the {role} Service send a cancellation request for the RTP')
@given('the {role} Service sent a cancellation request for the RTP')
def when_sp_cancel_rtp(context, role):
    cancel_response = cancel_rtp(context.access_tokens[role], context.latest_rtp_resource_id)
    context.cancel_rtp_response = cancel_response
    assert cancel_response.status_code == 204, f'Error cancelling RTP, got status code: {cancel_response.status_code}'


@when('the {role} Service send another cancellation request for the RTP')
def when_sp_cancel_rtp_again(context, role):
    cancel_response = cancel_rtp(context.access_tokens[role], context.latest_rtp_resource_id)
    context.cancel_rtp_response = cancel_response


@then('the RTP is already cancelled')
def then_rtp_already_cancelled(context):
    assert context.cancel_rtp_response.status_code == 422, f'Error cancelling RTP, got status code: {context.cancel_rtp_response.status_code}'


@then('the RTP is cancelled')
def then_rtp_is_cancelled(context):
    assert context.cancel_rtp_response.status_code == 204, f'Expected RTP to be cancelled, got status code: {context.cancel_rtp_response.status_code}'


@when('the {role} Service Provider send a cancellation request for a non-existing RTP')
def then_rtp_already_cancelled(context, role):
    cancel_response = cancel_rtp(context.access_tokens[role], str(uuid.uuid4()))
    context.latest_cancel_response = cancel_response

@then('the RTP is not found')
def then_rtp_is_not_found(context):
    assert context.latest_cancel_response.status_code == 404, f'Expected to not find the RTP, got status code: {context.latest_cancel_response.status_code}'
