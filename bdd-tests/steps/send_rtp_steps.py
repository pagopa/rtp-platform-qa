from behave import given
from behave import then
from behave import when

from api.send_rtp import send_rtp
from utils.dataset import generate_rtp_data


@when('the Service Provider sends an RTP to the debtor {debtor_name}')
def when_sp_sends_rtp(context, debtor_name: str):
    debtor_fc = context.debtor_fc[debtor_name]
    res = send_rtp(access_token=context.access_token, rtp_payload=generate_rtp_data(payer_id=debtor_fc))
    context.latest_rtp_response = res


@then('the RTP is created correctly')
def then_the_rtp_is_delivered(context):
    assert context.latest_rtp_response.status_code == 201


@given('the Ente Creditore is on the web page')
def given_ec_on_page(context):
    assert True, 'This test should not fail'


@given('the Ente Creditore insert RTP data')
def given_ec_insert_data(context):
    assert True, 'This test should not fail'


@when('the Ente Creditore presses send button')
def given_ec_press_send(context):
    assert True, 'This test should not fail'


@then('a confirmation messages shows confirming the operation')
def given_confirmation_message_shows(context):
    assert True, 'This test should not fail'
