import allure
import pytest

from utils.constants_epc_cancel_mock import (
    CANCEL_ERROR_INTERNAL_SERVER,
    CANCEL_ERROR_INVALID_RESPONSE,
    MOCK_CANCEL_NOTICE_NUMBER_400,
    MOCK_CANCEL_NOTICE_NUMBER_401,
    MOCK_CANCEL_NOTICE_NUMBER_404,
    MOCK_CANCEL_NOTICE_NUMBER_406,
    MOCK_CANCEL_NOTICE_NUMBER_410,
    MOCK_CANCEL_NOTICE_NUMBER_415,
    MOCK_CANCEL_NOTICE_NUMBER_422,
    MOCK_CANCEL_NOTICE_NUMBER_429,
    MOCK_CANCEL_NOTICE_NUMBER_500,
    MOCK_CANCEL_NOTICE_NUMBER_502,
    MOCK_CANCEL_NOTICE_NUMBER_503,
    MOCK_CANCEL_NOTICE_NUMBER_504,
    MOCK_CANCEL_NOTICE_NUMBER_CNCL,
    MOCK_CANCEL_NOTICE_NUMBER_CNCL_EXTRA_FIELD,
    MOCK_CANCEL_NOTICE_NUMBER_EMPTY_OBJECT,
    MOCK_CANCEL_NOTICE_NUMBER_MALFORMED_STRING,
    MOCK_CANCEL_NOTICE_NUMBER_MINIMAL_JSON,
    MOCK_CANCEL_NOTICE_NUMBER_NO_MATCH,
    MOCK_CANCEL_NOTICE_NUMBER_NO_STS_BLOCK,
    MOCK_CANCEL_NOTICE_NUMBER_PLAIN_STRING,
    MOCK_CANCEL_NOTICE_NUMBER_RJCR,
    MOCK_CANCEL_NOTICE_NUMBER_RJCR_EXTRA_FIELD,
    RTP_STATUS_CANCELLED_ACCR,
    RTP_STATUS_CANCELLED_REJECTED,
    RTP_STATUS_ERROR_CANCEL,
    RTP_STATUS_RFC_SENT,
)
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.constants_text_helper import CANCEL_REASON_PAID
from utils.rtp_cancel_helpers import send_and_cancel_rtp_v2_get_status

# Each entry: (scenario_id, notice_number, expected_status, description).
# These are cases where the cancel REST call itself is accepted (204) and the RTP either
# reaches a terminal cancellation status (CNCL/RJCR confirmed, unknown fields in the EPC
# response are tolerated) or stays in RFC_SENT because the EPC mock response carries no
# cancellation confirmation.
_HAPPY_PATH_SCENARIOS = [
    pytest.param(
        "empty_json_object",
        MOCK_CANCEL_NOTICE_NUMBER_EMPTY_OBJECT,
        RTP_STATUS_RFC_SENT,
        "No `Sts.Conf` confirmation is present (empty JSON object), so only CANCEL_RTP is "
        "triggered and the RTP stays in RFC_SENT.",
        id="empty_json_object",
    ),
    pytest.param(
        "plain_string",
        MOCK_CANCEL_NOTICE_NUMBER_PLAIN_STRING,
        RTP_STATUS_RFC_SENT,
        "The response body is not a recognizable cancellation confirmation (quoted plain "
        "string), so the RTP stays in RFC_SENT.",
        id="plain_string",
    ),
    pytest.param(
        "minimal_json",
        MOCK_CANCEL_NOTICE_NUMBER_MINIMAL_JSON,
        RTP_STATUS_RFC_SENT,
        "No `Sts.Conf` confirmation is present (minimal JSON without Sts), so only CANCEL_RTP "
        "is triggered and the RTP stays in RFC_SENT.",
        id="minimal_json",
    ),
    pytest.param(
        "cncl_confirmed",
        MOCK_CANCEL_NOTICE_NUMBER_CNCL,
        RTP_STATUS_CANCELLED_ACCR,
        '`Sts.Conf = "CNCL"` triggers CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_ACCR, ending in CANCELLED_ACCR.',
        id="cncl_confirmed",
    ),
    pytest.param(
        "rjcr_rejected",
        MOCK_CANCEL_NOTICE_NUMBER_RJCR,
        RTP_STATUS_CANCELLED_REJECTED,
        '`Sts.Conf = "RJCR"` triggers CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_REJECTED, ending in CANCELLED_REJECTED.',
        id="rjcr_rejected",
    ),
    pytest.param(
        "cncl_extra_field",
        MOCK_CANCEL_NOTICE_NUMBER_CNCL_EXTRA_FIELD,
        RTP_STATUS_CANCELLED_ACCR,
        '`Sts.Conf = "CNCL"` with an extra field not declared in the OpenAPI spec: the unknown '
        "field is ignored, so CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_ACCR is triggered, ending "
        "in CANCELLED_ACCR.",
        id="cncl_extra_field",
    ),
    pytest.param(
        "rjcr_extra_field",
        MOCK_CANCEL_NOTICE_NUMBER_RJCR_EXTRA_FIELD,
        RTP_STATUS_CANCELLED_REJECTED,
        '`Sts.Conf = "RJCR"` with an extra field not declared in the OpenAPI spec: the unknown '
        "field is ignored, so CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_REJECTED is triggered, "
        "ending in CANCELLED_REJECTED.",
        id="rjcr_extra_field",
    ),
    pytest.param(
        "no_match_fallback",
        MOCK_CANCEL_NOTICE_NUMBER_NO_MATCH,
        RTP_STATUS_RFC_SENT,
        "The mock policy falls back to its default `{}` response when no notice number "
        "matches, so the RTP stays in RFC_SENT.",
        id="no_match_fallback",
    ),
]


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP - EPC v4 mock happy path scenario: {scenario_id}")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
@pytest.mark.parametrize("scenario_id, notice_number, expected_status, description", _HAPPY_PATH_SCENARIOS)
def test_cancel_rtp_v2_epc_mock_happy_path(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
    scenario_id,
    notice_number,
    expected_status,
    description,
):
    """Cancel an RTP (v2) against an EPC v4 mock scenario where the cancel call is accepted (204)
    and assert the resulting RTP status.
    """
    allure.dynamic.description(description)

    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        notice_number,
        CANCEL_REASON_PAID,
        service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert status == expected_status, f"Expected status {expected_status}, got {status}"


# Each entry: (scenario_id, notice_number, expected_cancel_status, expected_error_code,
#              expected_status, description).
# These are cases where the PSP synchronously rejects the cancel call itself and the RTP ends
# in ERROR_CANCEL:
#   - EPC 4xx error responses -> 422 with code 02031008E (Service Provider invalid response);
#   - EPC 5xx error responses -> 500 with code 02091000F (Internal server error);
#   - EPC 2xx responses that are not a valid cancellation confirmation (CNCL without Sts
#     block, unquoted plain string) -> 422 with code 02031008E (Service Provider invalid response).
_UNHAPPY_PATH_SCENARIOS = [
    pytest.param(
        "epc_400",
        MOCK_CANCEL_NOTICE_NUMBER_400,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 400 "
        "Bad Request scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_400",
    ),
    pytest.param(
        "epc_401",
        MOCK_CANCEL_NOTICE_NUMBER_401,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 401 "
        "Unauthorized scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_401",
    ),
    pytest.param(
        "epc_404",
        MOCK_CANCEL_NOTICE_NUMBER_404,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 404 "
        "Not Found scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_404",
    ),
    pytest.param(
        "epc_406",
        MOCK_CANCEL_NOTICE_NUMBER_406,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 406 "
        "Not Acceptable scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_406",
    ),
    pytest.param(
        "epc_410",
        MOCK_CANCEL_NOTICE_NUMBER_410,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 410 "
        "Gone scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_410",
    ),
    pytest.param(
        "epc_415",
        MOCK_CANCEL_NOTICE_NUMBER_415,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 415 "
        "Unsupported Media Type scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_415",
    ),
    pytest.param(
        "epc_422",
        MOCK_CANCEL_NOTICE_NUMBER_422,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 422 "
        "Unprocessable Entity scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_422",
    ),
    pytest.param(
        "epc_429",
        MOCK_CANCEL_NOTICE_NUMBER_429,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (EPC 429 "
        "Too Many Requests scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_429",
    ),
    pytest.param(
        "epc_500",
        MOCK_CANCEL_NOTICE_NUMBER_500,
        500,
        CANCEL_ERROR_INTERNAL_SERVER,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 500 (EPC 500 "
        "Internal Server Error scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_500",
    ),
    pytest.param(
        "epc_502",
        MOCK_CANCEL_NOTICE_NUMBER_502,
        500,
        CANCEL_ERROR_INTERNAL_SERVER,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 500 (EPC 502 "
        "Bad Gateway scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_502",
    ),
    pytest.param(
        "epc_503",
        MOCK_CANCEL_NOTICE_NUMBER_503,
        500,
        CANCEL_ERROR_INTERNAL_SERVER,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 500 (EPC 503 "
        "Service Unavailable scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_503",
    ),
    pytest.param(
        "epc_504",
        MOCK_CANCEL_NOTICE_NUMBER_504,
        500,
        CANCEL_ERROR_INTERNAL_SERVER,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 500 (EPC 504 "
        "Gateway Timeout scenario). The RTP then transitions to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_504",
    ),
    pytest.param(
        "no_sts_block",
        MOCK_CANCEL_NOTICE_NUMBER_NO_STS_BLOCK,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The EPC response confirms the cancellation but omits the Sts block entirely, so it is "
        "treated as an invalid Service Provider response: the cancel call is rejected with 422 "
        "and the RTP transitions to ERROR_CANCEL.",
        id="no_sts_block",
    ),
    pytest.param(
        "malformed_string",
        MOCK_CANCEL_NOTICE_NUMBER_MALFORMED_STRING,
        422,
        CANCEL_ERROR_INVALID_RESPONSE,
        RTP_STATUS_ERROR_CANCEL,
        "The EPC response is a malformed, unquoted plain string that cannot be parsed, so it is "
        "treated as an invalid Service Provider response: the cancel call is rejected with 422 "
        "and the RTP transitions to ERROR_CANCEL.",
        id="malformed_string",
    ),
]


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP - EPC v4 mock unhappy path scenario: {scenario_id}")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    "scenario_id, notice_number, expected_cancel_status, expected_error_code, expected_status, description",
    _UNHAPPY_PATH_SCENARIOS,
)
def test_cancel_rtp_v2_epc_mock_unhappy_path(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
    scenario_id,
    notice_number,
    expected_cancel_status,
    expected_error_code,
    expected_status,
    description,
):
    """Cancel an RTP (v2) against an EPC v4 mock error/edge-case scenario and assert both the
    cancel call's HTTP status (and error code, when set) and the resulting RTP status.
    """
    allure.dynamic.description(description)

    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_c,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        notice_number,
        CANCEL_REASON_PAID,
        expected_cancel_status=expected_cancel_status,
        service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
        expected_error_code=expected_error_code,
    )
    assert status == expected_status, f"Expected status {expected_status}, got {status}"
