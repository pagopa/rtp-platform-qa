from uuid import uuid4

import allure
import pytest

from api.RTP_send_api import status_update_cancel_rtp_v2
from utils.constants_epc_status_update_cancel_mock import (
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_400,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_400_EMPTY_BODY,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_401,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_404,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_406,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_410,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_415,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_422,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_429,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_500,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_502,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_503,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_504,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_AEXR,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_MALFORMED_REASON,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCAR,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCNR,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCPR,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_TRUNCATED_JSON,
    MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_UNKNOWN_REASON,
    RTP_EVENT_RFC_NOT_RECEIVED,
    RTP_STATUS_CANCELLED_REJECTED,
    RTP_STATUS_EXPIRED,
    RTP_STATUS_RFC_SENT,
    RTP_STATUS_SENT,
    STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_RESPONSE,
    STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_TRANSITION,
    STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_RTP_NOT_FOUND,
    STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER,
    STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
    STATUS_UPDATE_CANCEL_ERROR_INVALID_RESPONSE,
    STATUS_UPDATE_CANCEL_ERROR_INVALID_TRANSITION,
    STATUS_UPDATE_CANCEL_ERROR_RTP_NOT_FOUND,
    STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER,
    STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
)
from utils.dataset_status_update_rtp import generate_status_update_rtp_data
from utils.generators_utils import generate_notice_number
from utils.rtp_status_update_helpers import (
    StatusUpdateRtpContext,
    assert_rtp_last_trigger_event,
    assert_status_update_error_response,
    assert_status_update_result,
    update_rtp_cancel_status_v2,
)

STATUS_UPDATE_CANCEL_SUCCESS_SCENARIOS = [
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_AEXR,
        "AEXR",
        RTP_STATUS_EXPIRED,
        id="aexr-expired",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCAR,
        "RCAR",
        RTP_STATUS_CANCELLED_REJECTED,
        id="rcar-cancelled-rejected",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCNR,
        "RCNR",
        RTP_STATUS_RFC_SENT,
        id="rcnr-no-transition",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCPR,
        "RCPR",
        RTP_STATUS_RFC_SENT,
        id="rcpr-no-transition",
    ),
    pytest.param(
        None,
        None,
        RTP_STATUS_RFC_SENT,
        id="fallback-no-match",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP status update cancel")
@allure.story("The EPC service provider returns a successful status-update cancel response")
@allure.title("A status-update cancel response maps to the expected RTP result")
@allure.tag("functional", "happy_path", "rtp_status_update_cancel", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
@pytest.mark.parametrize(
    "notice_number, expected_reason, expected_rtp_status",
    STATUS_UPDATE_CANCEL_SUCCESS_SCENARIOS,
)
def test_status_update_cancel_rtp_mock_success_scenarios(
    status_update_cancel_rtp_factory,
    random_fiscal_code,
    notice_number,
    expected_reason,
    expected_rtp_status,
):
    context = status_update_cancel_rtp_factory(
        payer_id=random_fiscal_code,
        # A notice number outside the mock scenarios gets a response without reason.
        notice_number=notice_number or generate_notice_number(),
        expected_final_status=expected_rtp_status,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=200,
        expected_rtp_status=expected_rtp_status,
        expected_reason=expected_reason,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update cancel")
@allure.story("The EPC service provider returns RCNR and the RTP keeps waiting for the cancellation outcome")
@allure.title("An RCNR status update cancel records RFC_NOT_RECEIVED and keeps the RTP in RFC_SENT")
@allure.tag("functional", "happy_path", "rtp_status_update_cancel", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
def test_status_update_cancel_rtp_mock_rcnr_records_rfc_not_received_event(
    status_update_cancel_rtp_factory,
    random_fiscal_code,
    rtp_reader_access_token,
):
    context = status_update_cancel_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCNR,
        expected_final_status=RTP_STATUS_RFC_SENT,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=200,
        expected_rtp_status=RTP_STATUS_RFC_SENT,
        expected_reason="RCNR",
    )
    assert_rtp_last_trigger_event(
        reader_token=rtp_reader_access_token,
        resource_id=context.resource_id,
        expected_trigger_event=RTP_EVENT_RFC_NOT_RECEIVED,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update cancel")
@allure.story("The RTP has no pending request for cancellation")
@allure.title("A status update cancel on an RTP not in RFC_SENT is rejected")
@allure.tag("functional", "unhappy_path", "rtp_status_update_cancel", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_status_update_cancel_rtp_mock_rejects_invalid_transition(
    status_update_rtp_resource_factory,
    random_fiscal_code,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    created_context = status_update_rtp_resource_factory(
        payer_id=random_fiscal_code,
        notice_number=MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_RCAR,
    )

    status_update_response, final_status = update_rtp_cancel_status_v2(
        creditor_token=creditor_service_provider_token_a,
        reader_token=rtp_reader_access_token,
        resource_id=created_context.resource_id,
        expected_final_status=RTP_STATUS_SENT,
    )
    context = StatusUpdateRtpContext(
        resource_id=created_context.resource_id,
        initial_status=created_context.initial_status,
        final_status=final_status,
        status_update_response=status_update_response,
    )
    assert_status_update_result(
        context=context,
        expected_response_status=422,
        expected_rtp_status=RTP_STATUS_SENT,
        expected_error_code=STATUS_UPDATE_CANCEL_ERROR_INVALID_TRANSITION,
        expected_error_description=STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_TRANSITION,
    )


STATUS_UPDATE_CANCEL_ERROR_SCENARIOS = [
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_400,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-400",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_401,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-401",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_404,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-404",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_406,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-406",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_410,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-410",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_415,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-415",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_422,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-422",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_429,
        422,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-429",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_UNKNOWN_REASON,
        422,
        STATUS_UPDATE_CANCEL_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="unknown-reason",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_500,
        500,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-500",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_502,
        500,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-502",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_503,
        500,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-503",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_504,
        500,
        STATUS_UPDATE_CANCEL_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-504",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_400_EMPTY_BODY,
        422,
        STATUS_UPDATE_CANCEL_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="empty-provider-error-body",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_MALFORMED_REASON,
        422,
        STATUS_UPDATE_CANCEL_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="malformed-reason",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_CANCEL_NOTICE_NUMBER_TRUNCATED_JSON,
        422,
        STATUS_UPDATE_CANCEL_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="truncated-json",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP status update cancel")
@allure.story("The EPC service provider returns an error or malformed response")
@allure.title("A status-update cancel error is normalized without changing the RTP")
@allure.tag("functional", "unhappy_path", "rtp_status_update_cancel", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    "notice_number, expected_response_status, expected_error_code, expected_error_description",
    STATUS_UPDATE_CANCEL_ERROR_SCENARIOS,
)
def test_status_update_cancel_rtp_mock_error_scenarios(
    status_update_cancel_rtp_factory,
    random_fiscal_code,
    notice_number,
    expected_response_status,
    expected_error_code,
    expected_error_description,
):
    context = status_update_cancel_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=notice_number,
        expected_final_status=RTP_STATUS_RFC_SENT,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=expected_response_status,
        expected_rtp_status=RTP_STATUS_RFC_SENT,
        expected_error_code=expected_error_code,
        expected_error_description=expected_error_description,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update cancel")
@allure.story("The requested RTP does not exist")
@allure.title("Requesting a status update cancel for an unknown RTP returns not found")
@allure.tag("functional", "unhappy_path", "rtp_status_update_cancel", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_status_update_cancel_rtp_unknown_resource(
    creditor_service_provider_token_a,
):
    response = status_update_cancel_rtp_v2(
        access_token=creditor_service_provider_token_a,
        status_update_payload=generate_status_update_rtp_data(str(uuid4())),
    )

    assert_status_update_error_response(
        response=response,
        expected_response_status=404,
        expected_error_code=STATUS_UPDATE_CANCEL_ERROR_RTP_NOT_FOUND,
        expected_error_description=STATUS_UPDATE_CANCEL_ERROR_DESCRIPTION_RTP_NOT_FOUND,
    )
