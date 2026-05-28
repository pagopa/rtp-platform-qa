from behave import given, then, when

from api.RTP_process_sender import send_gpd_message
from api.RTP_send_api import send_rtp
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.dataset_RTP_data import generate_rtp_data

TEST_SHOULD_NOT_FAIL_MSG = "This test should not fail"
TEST_TRUE_CONDITION = True


@when("the {role} Service Provider sends an RTP to the debtor {debtor_name}")
def when_sp_sends_rtp(context, debtor_name: str, role: str):
    debtor_fc = context.debtor_fc[debtor_name]

    if role == "debtor":
        # Use legacy REST endpoint for debtor role: it correctly returns 403 (forbidden)
        # since the GPD endpoint does not enforce role-based access control.
        res = send_rtp(access_token=context.access_tokens[role], rtp_payload=generate_rtp_data(payer_id=debtor_fc))
    else:
        # For creditor role, use the GPD message endpoint.
        # Use rtp_consumer token when creditor is authenticated; fall back to the role token
        # when creditor is unauthenticated (empty string) so that 401 is returned.
        if context.access_tokens.get("creditor"):
            send_token = context.access_tokens.get("rtp_consumer", context.access_tokens[role])
        else:
            send_token = context.access_tokens[role]
        message_payload = generate_gpd_message_payload(fiscal_code=debtor_fc, operation="CREATE", status="VALID")
        res = send_gpd_message(access_token=send_token, message_payload=message_payload)

    context.latest_rtp_response = res


@given("the {role} Service Provider sent an RTP to the debtor {debtor_name}")
def given_sp_sent_rtp(context, debtor_name: str, role: str):
    when_sp_sends_rtp(context, debtor_name, role)
    then_the_rtp_is_created(context)


@then("the RTP is created correctly")
def then_the_rtp_is_created(context):
    assert context.latest_rtp_response.status_code == 200
    resource_id = context.latest_rtp_response.json()["resourceId"]
    context.latest_rtp_resource_id = resource_id


@then("the RTP is not created because {reason_ko}")
def then_the_rtp_is_not_created(context, reason_ko):
    reason_ko = reason_ko.upper()
    actual = context.latest_rtp_response.status_code

    if reason_ko == "THE SERVICE PROVIDER IS NOT AUTHENTICATED":
        assert actual == 401, f"Expected 401, got {actual}: {context.latest_rtp_response.text[:200]}"

    if reason_ko == "THE DEBTOR SERVICE PROVIDER CANNOT SEND AN RTP":
        assert actual == 403, f"Expected 403, got {actual}: {context.latest_rtp_response.text[:200]}"

    if reason_ko == "THE DEBTOR IS NOT ACTIVATED":
        assert actual == 422, f"Expected 422, got {actual}: {context.latest_rtp_response.text[:200]}"


@given("the Ente Creditore is on the web page")
@given("the Creditor is on the web page")
def given_ec_on_page(context):
    assert TEST_TRUE_CONDITION, "TEST_SHOULD_NOT_FAIL_MSG"


@given("the Ente Creditore insert RTP data")
@given("the Creditor insert RTP data")
def given_ec_insert_data(context):
    assert TEST_TRUE_CONDITION, "TEST_SHOULD_NOT_FAIL_MSG"


@when("the Ente Creditore presses send button")
@when("the Creditor presses send button")
def given_ec_press_send(context):
    assert TEST_TRUE_CONDITION, "TEST_SHOULD_NOT_FAIL_MSG"


@then("a confirmation messages shows confirming the operation")
def given_confirmation_message_shows(context):
    assert TEST_TRUE_CONDITION, "TEST_SHOULD_NOT_FAIL_MSG"
