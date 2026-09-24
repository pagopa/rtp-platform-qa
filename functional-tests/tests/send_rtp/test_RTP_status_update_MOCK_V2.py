import allure
import pytest

from config.configuration import secrets
from utils.constants_epc_status_update_mock import (
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_AEXR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ALAC,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARFR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARJR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_IRNR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_NO_MATCH,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_REPR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_RSPR,
    RTP_STATUS_ERROR_SEND,
    RTP_STATUS_EXPIRED,
    RTP_STATUS_REJECTED,
    RTP_STATUS_SENT,
    RTP_STATUS_USER_ACCEPTED,
    RTP_STATUS_USER_REJECTED,
)
from utils.rtp_status_update_helpers import (
    assert_status_update_result,
    send_and_status_update_rtp_v2,
)


STATUS_UPDATE_SUCCESS_SCENARIOS = [
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_AEXR,
        "AEXR",
        RTP_STATUS_EXPIRED,
        id="aexr-expired",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_ALAC,
        "ALAC",
        RTP_STATUS_USER_ACCEPTED,
        id="alac-user-accepted",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARFR,
        "ARFR",
        RTP_STATUS_USER_REJECTED,
        id="arfr-user-rejected",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARJR,
        "ARJR",
        RTP_STATUS_REJECTED,
        id="arjr-rejected",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_IRNR,
        "IRNR",
        RTP_STATUS_ERROR_SEND,
        id="irnr-error-send",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_REPR,
        "REPR",
        RTP_STATUS_SENT,
        id="repr-no-transition",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_RSPR,
        "RSPR",
        RTP_STATUS_SENT,
        id="rspr-no-transition",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_NO_MATCH,
        None,
        RTP_STATUS_SENT,
        id="fallback-no-match",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The EPC service provider returns a successful status-update response")
@allure.title("A status-update response maps to the expected RTP result")
@allure.tag("functional", "happy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
@pytest.mark.parametrize(
    "notice_number, expected_reason, expected_rtp_status",
    STATUS_UPDATE_SUCCESS_SCENARIOS,
)
def test_status_update_rtp_mock_success_scenarios(
    debtor_service_provider_token_c,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    notice_number,
    expected_reason,
    expected_rtp_status,
):
    context = send_and_status_update_rtp_v2(
        debtor_token=debtor_service_provider_token_c,
        creditor_token=creditor_service_provider_token_a,
        reader_token=rtp_reader_access_token,
        payer_id=secrets.mock_actc_fiscal_code_v2,
        notice_number=notice_number,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=200,
        expected_rtp_status=expected_rtp_status,
        expected_reason=expected_reason,
    )
