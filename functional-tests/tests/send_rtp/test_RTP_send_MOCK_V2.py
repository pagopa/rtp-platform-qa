import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_send_api import send_rtp_v2
from config.configuration import config, secrets
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_RTP_data import generate_rtp_data
from utils.fiscal_code_utils import fake_fc
from utils.regex_utils import uuidv4_pattern
from utils.rtp_send_helpers import (
    send_rtp_v2_and_get_status_via_rest,
)

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
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    activation_response = activate(
        debtor_service_provider_token_c,
        random_fiscal_code,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code in (201, 409), (
        f"Error activating debtor: {activation_response.status_code} {activation_response.text}"
    )

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
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
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
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
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
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_no_links_fiscal_code_v2,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with a synchronous ACTC response containing an unexpected field")
@allure.title("An RTP sent when EPC ACTC response contains an unknown field is in status ACCEPTED - through Web API V2")
@allure.tag("functional", "happy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_extra_field_THROUGH_WEB_API_V2(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_extra_field_fiscal_code_v2,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response containing extra fields")
@allure.title(
    "An RTP sent with synchronous rejection containing extra fields results in status REJECTED - through Web API V2"
)
@allure.tag("functional", "happy_path", "rtp_send", "mock_rjct_extra_fields")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_rejected_with_extra_fields_THROUGH_WEB_API_V2(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
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
@allure.tag("functional", "happy_path", "rtp_send", "mock_rjct_no_links")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_rejected_no_links_THROUGH_WEB_API_V2(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_v2_and_get_status_via_rest(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_no_links_fiscal_code_v2,
    )
    assert status == "REJECTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with a malformed synchronous EPC response")
@allure.title("Sending an RTP when EPC returns a malformed/invalid response body returns 500 - through Web API V2")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_400_invalid_response")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_invalid_response_THROUGH_WEB_API_V2(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
):
    payer_id = secrets.mock_invalid_response_fiscal_code_v2

    activation_response = activate(
        debtor_service_provider_token_c,
        payer_id,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code in (201, 409), (
        f"Error activating debtor: {activation_response.status_code} {activation_response.text}"
    )

    rtp_data = generate_rtp_data(payer_id=payer_id)
    send_response = send_rtp_v2(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 500
    assert send_response.json()["code"] == "02091000F"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with an unexpected synchronous EPC error response")
@allure.title(
    "Sending an RTP when EPC returns an unexpected status code error (RTP_05.CHK.A0007) returns 500 "
    "- through Web API V2"
)
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_400_chk_a0007")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_unexpected_status_error_THROUGH_WEB_API_V2(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
):
    payer_id = secrets.mock_chk_error_fiscal_code_v2

    activation_response = activate(
        debtor_service_provider_token_c,
        payer_id,
        DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert activation_response.status_code in (201, 409), (
        f"Error activating debtor: {activation_response.status_code} {activation_response.text}"
    )

    rtp_data = generate_rtp_data(payer_id=payer_id)
    send_response = send_rtp_v2(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 500
    assert send_response.json()["code"] == "02091000F"
