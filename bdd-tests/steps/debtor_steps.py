from behave import then


@then('the debtor {debtor_name} is activated')
def then_the_debtor_is_activated(context, debtor_name):
    pass


@then('the debtor {debtor_name} receives the RTP')
def then_the_rtp_is_created(context, debtor_name):
    pass
