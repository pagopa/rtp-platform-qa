"""Tests for RTP cancellation (v2) against the EPC v4 cancellation mock scenarios.

Each test triggers a dedicated mock scenario on `postRequestToPayCancellationRequest-v4`
(see pagopa/cstar-securehub-infra-api-spec, mock_policy_cancel_epc_v4.xml) by forcing a
specific notice number on the RTP, then asserts the RTP status once the async
rtp-sender-v2 cancellation flow has processed the EPC mock response.

NOTE: these assertions describe the *target* behaviour of rtp-sender-v2 once the sidecar
EPC proxy extracts the `Sts.Conf` confirmation (CNCL/RJCR) from the raw EPC response. This
extraction is implemented on branch `SRTP-1968-cancel-sidecar` (rtp-sender-v2, PR #26); until
that branch is merged, `EpcService.processCancelRtp` on main does not populate the
`confirmation` field consumed by `SidecarCancelRtpHandler`, so all scenarios currently
resolve to RFC_SENT regardless of the mock response. These tests are expected to start
passing once that PR is merged.

Confirmed with rtp-sender-v2 maintainers (PR #26 review): an EPC response containing fields
not declared in the OpenAPI spec (cases 14/15, extra `invalid-field`) is intentionally treated
as an invalid message and is NOT tolerated for accept/reject purposes, so those cases expect
RFC_SENT rather than CANCELLED_ACCR/CANCELLED_REJECTED.
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
from utils.constants_text_helper import CANCEL_REASON_PAID
from utils.rtp_cancel_helpers import send_and_cancel_rtp_v2_get_status


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response is an empty JSON object leaves it in RFC_SENT")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_empty_json_object(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is empty JSON object and assert the resulting status.

    Expected outcome: no `Sts.Conf` confirmation is present, so only CANCEL_RTP is triggered and the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_EMPTY_OBJECT,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response is a quoted plain string leaves it in RFC_SENT")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_plain_string(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is quoted plain string and assert the resulting status.

    Expected outcome: the response body is not a recognizable cancellation confirmation, so the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_PLAIN_STRING,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response is minimal JSON without a Sts block leaves it in RFC_SENT")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_minimal_json(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is minimal JSON without Sts and assert the resulting status.

    Expected outcome: no `Sts.Conf` confirmation is present, so only CANCEL_RTP is triggered and the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_MINIMAL_JSON,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response confirms CNCL moves it to CANCELLED_ACCR")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_cncl_confirmed(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is Sts.Conf = CNCL and assert the resulting status.

    Expected outcome: `Sts.Conf = "CNCL"` triggers CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_ACCR, ending in CANCELLED_ACCR.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_CNCL,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_CANCELLED_ACCR, f"Expected status {RTP_STATUS_CANCELLED_ACCR}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response omits the Sts block entirely leaves it in RFC_SENT")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_no_sts_block(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is full response without Sts block and assert the resulting status.

    Expected outcome: no `Sts.Conf` confirmation is present, so only CANCEL_RTP is triggered and the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_NO_STS_BLOCK,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response confirms RJCR moves it to CANCELLED_REJECTED")
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_rjcr_rejected(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is Sts.Conf = RJCR and assert the resulting status.

    Expected outcome: `Sts.Conf = "RJCR"` triggers CANCEL_RTP -> CONFIRM_RFC -> CANCEL_RTP_REJECTED, ending in CANCELLED_REJECTED.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_RJCR,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_CANCELLED_REJECTED, f"Expected status {RTP_STATUS_CANCELLED_REJECTED}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 400 Bad Request moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_400(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 400 Bad Request and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_400,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 401 Unauthorized moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_401(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 401 Unauthorized and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_401,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 404 Not Found moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_404(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 404 Not Found and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_404,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 406 Not Acceptable moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_406(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 406 Not Acceptable and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_406,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 410 Gone moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_410(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 410 Gone and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_410,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 415 Unsupported Media Type moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_415(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 415 Unsupported Media Type and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_415,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 422 Unprocessable Entity moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_422(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 422 Unprocessable Entity and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_422,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock returns 429 Too Many Requests moves it to ERROR_CANCEL")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_epc_429(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is EPC 429 Too Many Requests and assert the resulting status.

    Expected outcome: any EPC HTTP error response triggers ERROR_CANCEL_RTP, ending in ERROR_CANCEL.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_429,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_ERROR_CANCEL, f"Expected status {RTP_STATUS_ERROR_CANCEL}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response confirms CNCL plus an unexpected field leaves it in RFC_SENT")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_cncl_extra_field(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is Sts.Conf = CNCL with unknown field and assert the resulting status.

    Expected outcome: an EPC response containing fields not declared in the OpenAPI spec is treated as an
    invalid message and is NOT tolerated for accept/reject purposes (confirmed with rtp-sender-v2
    maintainers, PR #26). The extra `invalid-field` property invalidates the whole response, so the
    CNCL confirmation is not processed and the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_CNCL_EXTRA_FIELD,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response confirms RJCR plus an unexpected field leaves it in RFC_SENT")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_rjcr_extra_field(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is Sts.Conf = RJCR with unknown field and assert the resulting status.

    Expected outcome: an EPC response containing fields not declared in the OpenAPI spec is treated as an
    invalid message and is NOT tolerated for accept/reject purposes (confirmed with rtp-sender-v2
    maintainers, PR #26). The extra `invalid-field` property invalidates the whole response, so the
    RJCR confirmation is not processed and the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_RJCR_EXTRA_FIELD,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title("Cancelling an RTP whose EPC mock response is a malformed, non-JSON string leaves it in RFC_SENT")
@allure.tag("functional", "unhappy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_cancel_rtp_v2_epc_mock_malformed_string(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is malformed unquoted string and assert the resulting status.

    Expected outcome: the response cannot be parsed as a cancellation confirmation, so the RTP stays in RFC_SENT rather than erroring out.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_MALFORMED_STRING,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"


@allure.epic("RTP Cancel")
@allure.feature("RTP Cancel")
@allure.story("Service provider cancels RTP - EPC v4 mock scenarios")
@allure.title(
    "Cancelling an RTP whose notice number matches no EPC mock scenario falls back to the default empty response, leaving it in RFC_SENT"
)
@allure.tag("functional", "happy_path", "rtp_cancel", "epc_v4_mock")
@pytest.mark.cancel
@pytest.mark.mock
@pytest.mark.happy_path
def test_cancel_rtp_v2_epc_mock_no_match_fallback(
    debtor_service_provider_token_a,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    random_fiscal_code,
):
    """
    Cancel an RTP (v2) whose EPC v4 mock response is no notice number match (default) and assert the resulting status.

    Expected outcome: the mock policy falls back to its default `{}` response when no notice number matches, so the RTP stays in RFC_SENT.
    """
    status = send_and_cancel_rtp_v2_get_status(
        debtor_service_provider_token_a,
        creditor_service_provider_token_a,
        rtp_reader_access_token,
        random_fiscal_code,
        MOCK_CANCEL_NOTICE_NUMBER_NO_MATCH,
        CANCEL_REASON_PAID,
    )
    assert status == RTP_STATUS_RFC_SENT, f"Expected status {RTP_STATUS_RFC_SENT}, got {status}"
