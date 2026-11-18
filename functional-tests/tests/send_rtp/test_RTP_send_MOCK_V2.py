import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_send_api import send_rtp_v2
from config.configuration import config
from utils.constants_epc_send_mock import (
    MOCK_SEND_FISCAL_CODE_400,
    MOCK_SEND_FISCAL_CODE_400_CHK_A0007,
    MOCK_SEND_FISCAL_CODE_400_TRUNCATED_JSON,
    MOCK_SEND_FISCAL_CODE_401,
    MOCK_SEND_FISCAL_CODE_404,
    MOCK_SEND_FISCAL_CODE_406,
    MOCK_SEND_FISCAL_CODE_410,
    MOCK_SEND_FISCAL_CODE_415,
    MOCK_SEND_FISCAL_CODE_422,
    MOCK_SEND_FISCAL_CODE_429,
    MOCK_SEND_FISCAL_CODE_500,
    MOCK_SEND_FISCAL_CODE_502,
    MOCK_SEND_FISCAL_CODE_502_NO_BODY,
    MOCK_SEND_FISCAL_CODE_503,
    MOCK_SEND_FISCAL_CODE_504,
    MOCK_SEND_FISCAL_CODE_ACTC,
    MOCK_SEND_FISCAL_CODE_ACTC_EXTRA_FIELD,
    MOCK_SEND_FISCAL_CODE_ACTC_NO_LINKS,
    MOCK_SEND_FISCAL_CODE_NON_JSON,
    MOCK_SEND_FISCAL_CODE_PROCESSED_STRING,
    MOCK_SEND_FISCAL_CODE_RJCT,
    MOCK_SEND_FISCAL_CODE_RJCT_EXTRA_FIELD,
    MOCK_SEND_FISCAL_CODE_RJCT_NO_LINKS,
    MOCK_SEND_FISCAL_CODE_SUCCESS_STRING,
    MOCK_SEND_FISCAL_CODE_TRUNCATED_JSON,
    RTP_STATUS_ACCEPTED,
    RTP_STATUS_REJECTED,
    RTP_STATUS_SENT,
    SEND_ERROR_INTERNAL_SERVER,
    SEND_ERROR_INVALID_RESPONSE,
)
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_RTP_data import generate_rtp_data
from utils.fiscal_code_utils import fake_fc
from utils.regex_utils import uuidv4_pattern
from utils.rtp_send_helpers import send_rtp_v2_get_status


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


# Each entry: (scenario_id, payer_fiscal_code, expected_status, description).
# These are cases where the send REST call itself is accepted (201) and the RTP either reaches a
# terminal status (ACTC -> ACCEPTED, RJCT -> REJECTED; unknown fields in the EPC response are
# tolerated) or stays in SENT because the EPC mock response carries no status report.
# A None fiscal code means a random one, which no mock branch matches.
_HAPPY_PATH_SCENARIOS = [
    pytest.param(
        "actc",
        MOCK_SEND_FISCAL_CODE_ACTC,
        RTP_STATUS_ACCEPTED,
        "EPC returns 201 with a complete ACTC report (with `_links`), so the RTP ends in ACCEPTED.",
        id="actc",
    ),
    pytest.param(
        "actc_no_links",
        MOCK_SEND_FISCAL_CODE_ACTC_NO_LINKS,
        RTP_STATUS_ACCEPTED,
        "EPC returns 201 with an ACTC report without `_links` (optional in the schema), so the RTP ends in ACCEPTED.",
        id="actc_no_links",
    ),
    pytest.param(
        "actc_extra_field",
        MOCK_SEND_FISCAL_CODE_ACTC_EXTRA_FIELD,
        RTP_STATUS_ACCEPTED,
        "EPC returns 201 with an ACTC report plus an extra field not declared in the schema: the "
        "unknown field is ignored and the RTP ends in ACCEPTED.",
        id="actc_extra_field",
    ),
    pytest.param(
        "rjct",
        MOCK_SEND_FISCAL_CODE_RJCT,
        RTP_STATUS_REJECTED,
        "EPC returns 400 with a valid RJCT report (reason MS03): the send call is accepted (201) "
        "and the RTP ends in REJECTED.",
        id="rjct",
    ),
    pytest.param(
        "rjct_no_links",
        MOCK_SEND_FISCAL_CODE_RJCT_NO_LINKS,
        RTP_STATUS_REJECTED,
        "EPC returns 400 with a valid RJCT report without `_links`: the send call is accepted "
        "(201) and the RTP ends in REJECTED.",
        id="rjct_no_links",
    ),
    pytest.param(
        "rjct_extra_field",
        MOCK_SEND_FISCAL_CODE_RJCT_EXTRA_FIELD,
        RTP_STATUS_REJECTED,
        "EPC returns 400 with a RJCT report plus an extra field not declared in the schema: the "
        "unknown field is ignored, the send call is accepted (201) and the RTP ends in REJECTED.",
        id="rjct_extra_field",
    ),
    pytest.param(
        "success_string",
        MOCK_SEND_FISCAL_CODE_SUCCESS_STRING,
        RTP_STATUS_SENT,
        'EPC returns 201 with the JSON string `"success"`, which carries no status report, so the RTP stays in SENT.',
        id="success_string",
    ),
    pytest.param(
        "processed_string",
        MOCK_SEND_FISCAL_CODE_PROCESSED_STRING,
        RTP_STATUS_SENT,
        'EPC returns 201 with the JSON string `"<uuid> processed correctly"`, which carries no '
        "status report, so the RTP stays in SENT.",
        id="processed_string",
    ),
    pytest.param(
        "no_match_fallback",
        None,
        RTP_STATUS_SENT,
        "No known fiscal code is in the request, so the mock policy falls back to its default 201"
        " `{}` response, which carries no status report: the RTP stays in SENT.",
        id="no_match_fallback",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends RTP - EPC v4 mock scenarios")
@allure.title("Sending an RTP - EPC v4 mock happy path scenario: {scenario_id}")
@allure.tag("functional", "happy_path", "rtp_send", "epc_v4_mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
@pytest.mark.parametrize("scenario_id, payer_fiscal_code, expected_status, description", _HAPPY_PATH_SCENARIOS)
def test_send_rtp_v2_epc_mock_happy_path(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
    scenario_id,
    payer_fiscal_code,
    expected_status,
    description,
):
    """Send an RTP (v2) against an EPC v4 mock scenario where the send call is accepted (201)
    and assert the resulting RTP status.
    """
    allure.dynamic.description(description)

    status = send_rtp_v2_get_status(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        payer_fiscal_code or random_fiscal_code,
        service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert status == expected_status, f"Expected status {expected_status}, got {status}"


# Each entry: (scenario_id, payer_fiscal_code, expected_send_status, expected_error_code,
#              expected_status, description).
# These are cases where the PSP synchronously rejects the send call itself:
#   - EPC 201 responses whose body cannot be parsed (non-JSON, truncated JSON) -> 422 with code
#     02031008E (Service Provider invalid response); the RTP stays in SENT;
#   - EPC 4xx/5xx error responses (standard or anomalous body) -> 500 with code 02091000F
#     (Internal server error); no RTP is persisted (expected_status None).
_UNHAPPY_PATH_SCENARIOS = [
    pytest.param(
        "non_json",
        MOCK_SEND_FISCAL_CODE_NON_JSON,
        422,
        SEND_ERROR_INVALID_RESPONSE,
        RTP_STATUS_SENT,
        "EPC returns 201 with a non-JSON body (`InvalidResponse`) that cannot be parsed: the send"
        " call is rejected with 422 (Service Provider invalid response) and the RTP stays in "
        "SENT.",
        id="non_json",
    ),
    pytest.param(
        "truncated_json",
        MOCK_SEND_FISCAL_CODE_TRUNCATED_JSON,
        422,
        SEND_ERROR_INVALID_RESPONSE,
        RTP_STATUS_SENT,
        'EPC returns 201 with a truncated JSON body (`{"InvalidResponse"`): the send call is '
        "rejected with 422 (Service Provider invalid response) and the RTP stays in SENT.",
        id="truncated_json",
    ),
    pytest.param(
        "epc_502_no_body",
        MOCK_SEND_FISCAL_CODE_502_NO_BODY,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 502 with no body: the send call is rejected with 500 (Internal server error)"
        " and no RTP is persisted.",
        id="epc_502_no_body",
    ),
    pytest.param(
        "epc_400_truncated_json",
        MOCK_SEND_FISCAL_CODE_400_TRUNCATED_JSON,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        'EPC returns 400 with a truncated JSON body (`{"InvalidResponse"`): the send call is '
        "rejected with 500 (Internal server error) and no RTP is persisted.",
        id="epc_400_truncated_json",
    ),
    pytest.param(
        "epc_400_chk_a0007",
        MOCK_SEND_FISCAL_CODE_400_CHK_A0007,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 400 with an RTP_05.CHK.A0007 error body whose status (500) does not match "
        "the HTTP status: the send call is rejected with 500 (Internal server error) and no RTP "
        "is persisted.",
        id="epc_400_chk_a0007",
    ),
    pytest.param(
        "epc_400",
        MOCK_SEND_FISCAL_CODE_400,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 400 Bad Request with a standard error body: the send call is rejected with "
        "500 (Internal server error) and no RTP is persisted.",
        id="epc_400",
    ),
    pytest.param(
        "epc_401",
        MOCK_SEND_FISCAL_CODE_401,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 401 Unauthorized with a standard error body: the send call is rejected with "
        "500 (Internal server error) and no RTP is persisted.",
        id="epc_401",
    ),
    pytest.param(
        "epc_404",
        MOCK_SEND_FISCAL_CODE_404,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 404 Not Found with a standard error body: the send call is rejected with 500"
        " (Internal server error) and no RTP is persisted.",
        id="epc_404",
    ),
    pytest.param(
        "epc_406",
        MOCK_SEND_FISCAL_CODE_406,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 406 Not Acceptable with a standard error body: the send call is rejected "
        "with 500 (Internal server error) and no RTP is persisted.",
        id="epc_406",
    ),
    pytest.param(
        "epc_410",
        MOCK_SEND_FISCAL_CODE_410,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 410 Gone with a standard error body: the send call is rejected with 500 "
        "(Internal server error) and no RTP is persisted.",
        id="epc_410",
    ),
    pytest.param(
        "epc_415",
        MOCK_SEND_FISCAL_CODE_415,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 415 Unsupported Media Type with a standard error body: the send call is "
        "rejected with 500 (Internal server error) and no RTP is persisted.",
        id="epc_415",
    ),
    pytest.param(
        "epc_422",
        MOCK_SEND_FISCAL_CODE_422,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 422 Unprocessable Entity with a standard error body: the send call is "
        "rejected with 500 (Internal server error) and no RTP is persisted.",
        id="epc_422",
    ),
    pytest.param(
        "epc_429",
        MOCK_SEND_FISCAL_CODE_429,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 429 Too Many Requests with a standard error body: the send call is rejected "
        "with 500 (Internal server error) and no RTP is persisted.",
        id="epc_429",
    ),
    pytest.param(
        "epc_500",
        MOCK_SEND_FISCAL_CODE_500,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 500 Internal Server Error with a standard error body: the send call is "
        "rejected with 500 (Internal server error) and no RTP is persisted.",
        id="epc_500",
    ),
    pytest.param(
        "epc_502",
        MOCK_SEND_FISCAL_CODE_502,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 502 Bad Gateway with a standard error body: the send call is rejected with "
        "500 (Internal server error) and no RTP is persisted.",
        id="epc_502",
    ),
    pytest.param(
        "epc_503",
        MOCK_SEND_FISCAL_CODE_503,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 503 Service Unavailable with a standard error body: the send call is "
        "rejected with 500 (Internal server error) and no RTP is persisted.",
        id="epc_503",
    ),
    pytest.param(
        "epc_504",
        MOCK_SEND_FISCAL_CODE_504,
        500,
        SEND_ERROR_INTERNAL_SERVER,
        None,
        "EPC returns 504 Gateway Timeout with a standard error body: the send call is rejected "
        "with 500 (Internal server error) and no RTP is persisted.",
        id="epc_504",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP Send")
@allure.story("Service provider sends RTP - EPC v4 mock scenarios")
@allure.title("Sending an RTP - EPC v4 mock unhappy path scenario: {scenario_id}")
@allure.tag("functional", "unhappy_path", "rtp_send", "epc_v4_mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    "scenario_id, payer_fiscal_code, expected_send_status, expected_error_code, expected_status, description",
    _UNHAPPY_PATH_SCENARIOS,
)
def test_send_rtp_v2_epc_mock_unhappy_path(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    scenario_id,
    payer_fiscal_code,
    expected_send_status,
    expected_error_code,
    expected_status,
    description,
):
    """Send an RTP (v2) against an EPC v4 mock error/edge-case scenario and assert both the send
    call's HTTP status and error code, and the resulting RTP status (None when no RTP is persisted).
    """
    allure.dynamic.description(description)

    status = send_rtp_v2_get_status(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        payer_fiscal_code,
        expected_send_status=expected_send_status,
        service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
        expected_error_code=expected_error_code,
    )
    assert status == expected_status, f"Expected status {expected_status}, got {status}"
