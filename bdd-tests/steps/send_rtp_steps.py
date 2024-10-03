from behave import given
from behave import when
from behave import then


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
