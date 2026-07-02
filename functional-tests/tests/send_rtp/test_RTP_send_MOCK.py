import allure
import pytest

from api.RTP_process_sender import send_gpd_message
from api.RTP_send_api import send_rtp, send_rtp_v2
from config.configuration import config, secrets
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.dataset_RTP_data import generate_rtp_data
from utils.fiscal_code_utils import fake_fc
from utils.regex_utils import uuidv4_pattern
from utils.rtp_send_helpers import (
    send_rtp_and_get_status,
    send_rtp_and_get_status_by_notice_number,
    send_rtp_and_get_status_by_notice_number_via_rest,
    send_rtp_and_get_status_via_rest,
    send_rtp_v2_and_get_status_via_rest,
    send_rtp_v2_and_get_status_by_notice_number_via_rest,
)


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("An RTP is sent through GPD message API")
@allure.tag("functional", "happy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api(rtp_consumer_access_token, activate_payer, random_fiscal_code):

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 200

    resource_id = send_response.json()["resourceId"]
    assert bool(uuidv4_pattern.fullmatch(resource_id)), f"resourceId is not a valid UUIDv4: {resource_id}"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("Sending a GPD message with null id returns 400")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_gpd_message_with_null_id(rtp_consumer_access_token, activate_payer, random_fiscal_code):

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")
    message_payload["id"] = None

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert response.status_code == 400


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("Sending a GPD message with null operation returns 400")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_field_error_in_body(rtp_consumer_access_token, activate_payer, random_fiscal_code):

    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")
    message_payload["operation"] = None

    response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert response.status_code == 400


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a non-activated debtor")
@allure.title("Sending to non-activated debtor returns 422")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_not_activated_user(rtp_consumer_access_token):

    message_payload = generate_gpd_message_payload(fiscal_code=fake_fc(), operation="CREATE", status="VALID")

    send_response = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert send_response.status_code == 422


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response")
@allure.title("An RTP sent with synchronous acceptance is in status ACCEPTED - DS-05 ACTC")
@allure.tag("functional", "happy_path", "rtp_send", "ds_05_actc")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_ds05_actc(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_actc_fiscal_code,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response")
@allure.title("An RTP sent with synchronous rejection is in status REJECTED - DS-08P N")
@allure.tag("functional", "happy_path", "rtp_send", "ds_08p_n")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_rejected_ds08p_n(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_rjct_fiscal_code,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response missing _links")
@allure.title("An RTP sent when EPC response omits _links is in status ACCEPTED")
@allure.tag("functional", "happy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_no_links(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_no_links_fiscal_code,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story(
    "Service provider sends an RTP with a non-compliant synchronous ACTC-like response containing an unexpected field that is ignored"
)
@allure.title("An RTP sent when EPC response contains an unknown field is ignored and remains in status SENT")
@allure.tag("functional", "unhappy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_sent_extra_field(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_extra_field_fiscal_code,
    )
    assert status == "SENT"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response containing extra fields")
@allure.title("An RTP sent with synchronous rejection containing extra fields results in status REJECTED")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_extra_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_with_extra_fields(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_rjct_extra_field_fiscal_code,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response without _links")
@allure.title("An RTP sent with synchronous rejection and missing _links results in status REJECTED")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_no_links")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_no_links(
    debtor_service_provider_token_a,
    rtp_consumer_access_token,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number(
        debtor_service_provider_token_a,
        rtp_consumer_access_token,
        rtp_reader_access_token,
        secrets.mock_rjct_no_links_fiscal_code,
    )
    assert status == "REJECTED"


# ── THROUGH_WEB_API variants ─────────────────────────────────────────────────
# These replicate the above tests using the legacy REST send endpoint (/rtps).


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("An RTP is sent through API - through Web API")
@allure.tag("functional", "happy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    rtp_data = generate_rtp_data(payer_id=random_fiscal_code)
    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert "/".join(location_split[:-1]) == config.rtp_creation_base_url_path + config.send_rtp_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a non-activated debtor")
@allure.title("Sending to non-activated debtor returns 422 - through Web API")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_not_activated_user_THROUGH_WEB_API(creditor_service_provider_token_a):
    rtp_data = generate_rtp_data(payer_id=fake_fc())
    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 422


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response")
@allure.title("An RTP sent with synchronous acceptance is in status ACCEPTED - DS-05 ACTC - through Web API")
@allure.tag("functional", "happy_path", "rtp_send", "ds_05_actc")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_ds05_actc_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_actc_fiscal_code,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response")
@allure.title("An RTP sent with synchronous rejection is in status REJECTED - DS-08P N - through Web API")
@allure.tag("functional", "happy_path", "rtp_send", "ds_08p_n")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_rejected_ds08p_n_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_fiscal_code,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response missing _links")
@allure.title("An RTP sent when EPC response omits _links is in status ACCEPTED - through Web API")
@allure.tag("functional", "happy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_no_links_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_no_links_fiscal_code,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story(
    "Service provider sends an RTP with a non-compliant synchronous ACTC-like response containing an unexpected field that is ignored"
)
@allure.title(
    "An RTP sent when EPC response contains an unknown field is ignored and remains in status SENT - through Web API"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_sent_extra_field_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_extra_field_fiscal_code,
    )
    assert status == "SENT"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response containing extra fields")
@allure.title(
    "An RTP sent with synchronous rejection containing extra fields results in status REJECTED - through Web API"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_extra_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_with_extra_fields_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_extra_field_fiscal_code,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response without _links")
@allure.title("An RTP sent with synchronous rejection and missing _links results in status REJECTED - through Web API")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_no_links")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_no_links_THROUGH_WEB_API(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_no_links_fiscal_code,
    )
    assert status == "REJECTED"


# ── THROUGH_WEB_API_V2 variants ──────────────────────────────────────────────
# These replicate the _THROUGH_WEB_API tests using the v2 REST send endpoint
# (same URL /rtps but with Version: v2 header).


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("An RTP is sent through API - through Web API V2")
@allure.tag("functional", "happy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    activate_payer,
    random_fiscal_code,
):
    activation_response = activate_payer(random_fiscal_code)
    assert activation_response.status_code == 201, "Error activating debtor"

    rtp_data = generate_rtp_data(payer_id=random_fiscal_code)
    send_response = send_rtp_v2(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert "/".join(location_split[:-1]) == config.rtp_creation_base_url_path + config.send_rtp_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a non-activated debtor")
@allure.title("Sending to non-activated debtor returns 422 - through Web API V2")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_not_activated_user_THROUGH_WEB_API_V2(creditor_service_provider_token_a):
    rtp_data = generate_rtp_data(payer_id=fake_fc())
    send_response = send_rtp_v2(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 422


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response")
@allure.title("An RTP sent with synchronous acceptance is in status ACCEPTED - DS-05 ACTC - through Web API V2")
@allure.tag("functional", "happy_path", "rtp_send", "ds_05_actc")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_ds05_actc_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_actc_fiscal_code_v2,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response")
@allure.title("An RTP sent with synchronous rejection is in status REJECTED - DS-08P N - through Web API V2")
@allure.tag("functional", "happy_path", "rtp_send", "ds_08p_n")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_rejected_ds08p_n_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_fiscal_code_v2,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response missing _links")
@allure.title("An RTP sent when EPC response omits _links is in status ACCEPTED - through Web API V2")
@allure.tag("functional", "happy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_no_links_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_no_links_fiscal_code_v2,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story(
    "Service provider sends an RTP with a non-compliant synchronous ACTC-like response containing an unexpected field that is ignored"
)
@allure.title(
    "An RTP sent when EPC response contains an unknown field is ignored and remains in status SENT - through Web API V2"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_sent_extra_field_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_extra_field_fiscal_code_v2,
    )
    assert status == "SENT"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response containing extra fields")
@allure.title(
    "An RTP sent with synchronous rejection containing extra fields results in status REJECTED - through Web API V2"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_extra_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_with_extra_fields_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_extra_field_fiscal_code_v2,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response without _links")
@allure.title(
    "An RTP sent with synchronous rejection and missing _links results in status REJECTED - through Web API V2"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_no_links")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_no_links_THROUGH_WEB_API_V2(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_by_notice_number_via_rest(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_no_links_fiscal_code_v2,
    )
    assert status == "REJECTED"
