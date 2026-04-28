import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_send_api import send_rtp
from config.configuration import config, secrets
from utils.dataset_RTP_data import generate_rtp_data
from utils.regex_utils import uuidv4_pattern
from utils.rtp_send_helpers import send_rtp_and_get_status, send_rtp_and_get_status_rejected


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("An RTP is sent through API")
@allure.tag("functional", "happy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api(debtor_service_provider_token_a, creditor_service_provider_token_a):

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    location_split = location.split("/")
    assert "/".join(location_split[:-1]) == config.rtp_creation_base_url_path + config.send_rtp_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("Debtor fiscal code must be lower case during RTP send")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_api_lower_fiscal_code(debtor_service_provider_token_a, creditor_service_provider_token_a):

    rtp_data = generate_rtp_data()

    res = activate(
        debtor_service_provider_token_a,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert res.status_code == 201, "Error activating debtor"

    rtp_data["payer"]["payerId"] = rtp_data["payer"]["payerId"].lower()
    response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert response.status_code == 400


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP")
@allure.title("The response body contains a comprehensible error message")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_field_error_in_body(debtor_service_provider_token_a, creditor_service_provider_token_a):

    rtp_data = generate_rtp_data()

    res = activate(
        debtor_service_provider_token_a,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert res.status_code == 201, "Error activating debtor"

    rtp_data["payee"]["payeeId"] = None
    response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert response.status_code == 400
    assert response.json()["error"] == "NotNull.createRtpDtoMono.payee.payeeId"
    assert response.json()["details"] == "payee.payeeId must not be null"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP to a non-activated debtor")
@allure.title("An RTP is sent through API")
@allure.tag("functional", "unhappy_path", "rtp_send")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_not_activated_user(creditor_service_provider_token_a):

    rtp_data = generate_rtp_data()

    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert send_response.status_code == 404


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous ACTC response")
@allure.title("An RTP sent with synchronous acceptance is in status ACCEPTED - DS-05 ACTC")
@allure.tag("functional", "happy_path", "rtp_send", "ds_05_actc")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_sync_accepted_ds05_actc(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
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
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status_rejected(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_rjct_fiscal_code,
        expected_send_status=422,
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
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_no_links_fiscal_code,
    )
    assert status == "ACCEPTED"


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with a non-compliant synchronous ACTC-like response containing an unexpected field that is ignored")
@allure.title("An RTP sent when EPC response contains an unknown field is ignored and remains in status SENT")
@allure.tag("functional", "unhappy_path", "rtp_send", "optional_epc_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_sent_extra_field(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    status = send_rtp_and_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_extra_field_fiscal_code,
    )
    assert status == "SENT"
    
@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response containing extra fields")
@allure.title("An RTP sent with synchronous rejection containing extra fields returns HTTP 422")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_extra_fields")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_with_extra_fields(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    expected_status: str = "REJECTED",
):
    status = send_rtp_and_get_status_rejected(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_reject_extra_fields_fiscal_code,
    )
    assert status == expected_status

@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends an RTP with synchronous RJCT response without _links")
@allure.title("An RTP sent with synchronous rejection and missing _links returns HTTP 422")
@allure.tag("functional", "unhappy_path", "rtp_send", "mock_422_rjct_no_links")
@pytest.mark.send
@pytest.mark.unhappy_path
def test_send_rtp_sync_rejected_no_links(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    expected_status: str = "REJECTED",
):
    status = send_rtp_and_get_status_rejected(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        secrets.mock_reject_no_links_fiscal_code,
    )
    assert status == expected_status
