"""Tests for RTP cancellation (v2) against the EPC v4 cancellation mock scenarios.

Each test triggers a dedicated mock scenario on `postRequestToPayCancellationRequest-v4`
(see pagopa/cstar-securehub-infra-api-spec, mock_policy_cancel_epc_v4.xml) by forcing a
specific notice number on the RTP, then asserts the RTP status once the async
rtp-sender-v2 cancellation flow has processed the EPC mock response.

PR #26 (`SRTP-1968-cancel-sidecar`, rtp-sender-v2) is merged and deployed: the sidecar EPC
proxy now extracts the `Sts.Conf` confirmation (CNCL/RJCR) from the raw EPC response.

Confirmed with rtp-sender-v2 maintainers (PR #26 review): an EPC response containing fields
not declared in the OpenAPI spec (cases 14/15, extra `invalid-field`) is intentionally treated
as an invalid message and is NOT tolerated for accept/reject purposes, so those cases expect
RFC_SENT rather than CANCELLED_ACCR/CANCELLED_REJECTED.

Confirmed with the team (Luigi De Marco, Francesco Muscianisi): for the EPC HTTP error
scenarios (cases 7-14, notice numbers ...006-...013), the PSP synchronously rejects the
cancel request itself with 422 ("Service Provider rejection") per standard for these error
codes, rather than accepting it with 204. The RTP is then checked and must end up in
ERROR_CANCEL.
"""

import allure
import pytest

from utils.constants_epc_cancel_mock import (
    MOCK_CANCEL_NOTICE_NUMBER_400,
    MOCK_CANCEL_NOTICE_NUMBER_401,
    MOCK_CANCEL_NOTICE_NUMBER_404,
    MOCK_CANCEL_NOTICE_NUMBER_406,
    MOCK_CANCEL_NOTICE_NUMBER_410,
    MOCK_CANCEL_NOTICE_NUMBER_415,
    MOCK_CANCEL_NOTICE_NUMBER_422,
    MOCK_CANCEL_NOTICE_NUMBER_429,
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
# reaches a terminal cancellation status (CNCL/RJCR confirmed) or stays in RFC_SENT because
# the EPC mock response carries no usable/parseable cancellation confirmation.
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
        "no_sts_block",
        MOCK_CANCEL_NOTICE_NUMBER_NO_STS_BLOCK,
        RTP_STATUS_RFC_SENT,
        "No `Sts.Conf` confirmation is present (Sts block omitted entirely), so only "
        "CANCEL_RTP is triggered and the RTP stays in RFC_SENT.",
        id="no_sts_block",
    ),
    pytest.param(
        "rjcr_rejected",
        MOCK_CANCEL_NOTICE_NUMBER_RJCR,
        RTP_STATUS_CANCELLED_REJECTED,
        '`Sts.Conf = "RJCR"` triggers CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_REJECTED, ending in CANCELLED_REJECTED.',
        id="rjcr_rejected",
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


# Each entry: (scenario_id, notice_number, expected_cancel_status, expected_status, description).
# These are cases where either the EPC mock HTTP error code causes the PSP to synchronously
# reject the cancel call itself (422), or the EPC mock response is malformed/carries an
# unexpected field and is treated as an invalid, non-actionable message (cancel call still
# accepted with 204, but the RTP stays in RFC_SENT).
_UNHAPPY_PATH_SCENARIOS = [
    pytest.param(
        "epc_400",
        MOCK_CANCEL_NOTICE_NUMBER_400,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 400 Bad Request scenario). The RTP then transitions to "
        "ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_400",
    ),
    pytest.param(
        "epc_401",
        MOCK_CANCEL_NOTICE_NUMBER_401,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 401 Unauthorized scenario). The RTP then transitions to "
        "ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_401",
    ),
    pytest.param(
        "epc_404",
        MOCK_CANCEL_NOTICE_NUMBER_404,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 404 Not Found scenario). The RTP then transitions to "
        "ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_404",
    ),
    pytest.param(
        "epc_406",
        MOCK_CANCEL_NOTICE_NUMBER_406,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 406 Not Acceptable scenario). The RTP then transitions to "
        "ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_406",
    ),
    pytest.param(
        "epc_410",
        MOCK_CANCEL_NOTICE_NUMBER_410,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 410 Gone scenario). The RTP then transitions to ERROR_CANCEL "
        "via ERROR_CANCEL_RTP.",
        id="epc_410",
    ),
    pytest.param(
        "epc_415",
        MOCK_CANCEL_NOTICE_NUMBER_415,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 415 Unsupported Media Type scenario). The RTP then transitions "
        "to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_415",
    ),
    pytest.param(
        "epc_422",
        MOCK_CANCEL_NOTICE_NUMBER_422,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 422 Unprocessable Entity scenario). The RTP then transitions "
        "to ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_422",
    ),
    pytest.param(
        "epc_429",
        MOCK_CANCEL_NOTICE_NUMBER_429,
        422,
        RTP_STATUS_ERROR_CANCEL,
        "The PSP synchronously rejects the cancellation request with 422 (per standard "
        "behaviour for the EPC 429 Too Many Requests scenario). The RTP then transitions to "
        "ERROR_CANCEL via ERROR_CANCEL_RTP.",
        id="epc_429",
    ),
    pytest.param(
        "cncl_extra_field",
        MOCK_CANCEL_NOTICE_NUMBER_CNCL_EXTRA_FIELD,
        204,
        RTP_STATUS_RFC_SENT,
        "An EPC response containing fields not declared in the OpenAPI spec is treated as an "
        "invalid message and is NOT tolerated for accept/reject purposes (confirmed with "
        "rtp-sender-v2 maintainers, PR #26). The extra `invalid-field` property invalidates "
        "the whole response, so the CNCL confirmation is not processed and the RTP stays in "
        "RFC_SENT.",
        id="cncl_extra_field",
    ),
    pytest.param(
        "rjcr_extra_field",
        MOCK_CANCEL_NOTICE_NUMBER_RJCR_EXTRA_FIELD,
        204,
        RTP_STATUS_RFC_SENT,
        "An EPC response containing fields not declared in the OpenAPI spec is treated as an "
        "invalid message and is NOT tolerated for accept/reject purposes (confirmed with "
        "rtp-sender-v2 maintainers, PR #26). The extra `invalid-field` property invalidates "
        "the whole response, so the RJCR confirmation is not processed and the RTP stays in "
        "RFC_SENT.",
        id="rjcr_extra_field",
    ),
    pytest.param(
        "malformed_string",
        MOCK_CANCEL_NOTICE_NUMBER_MALFORMED_STRING,
        204,
        RTP_STATUS_RFC_SENT,
        "The response cannot be parsed as a cancellation confirmation (malformed, unquoted "
        "string), so the RTP stays in RFC_SENT rather than erroring out.",
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
    "scenario_id, notice_number, expected_cancel_status, expected_status, description", _UNHAPPY_PATH_SCENARIOS
)
def test_cancel_rtp_v2_epc_mock_unhappy_path(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
    scenario_id,
    notice_number,
    expected_cancel_status,
    expected_status,
    description,
):
    """Cancel an RTP (v2) against an EPC v4 mock error/edge-case scenario and assert both the
    cancel call's HTTP status and the resulting RTP status.
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
    )
    assert status == expected_status, f"Expected status {expected_status}, got {status}"
