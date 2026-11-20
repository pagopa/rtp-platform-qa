from uuid import uuid4

import allure
import pytest

from api.RTP_callback_api import srtp_rfc_callback_v2
from api.RTP_cancel_api import cancel_rtp_v2
from api.RTP_send_api import status_update_rtp_v2
from utils.constants_epc_status_update_mock import (
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_400,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_401,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_404,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_406,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_410,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_415,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_422,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_429,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_500,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_502,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_503,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_504,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_AEXR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ALAC,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARFR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_ARJR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_EMPTY_BODY,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_IRNR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_MALFORMED_REASON,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_NO_MATCH,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_REPR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_RSPR,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_TRUNCATED_JSON,
    MOCK_STATUS_UPDATE_NOTICE_NUMBER_UNKNOWN_REASON,
    RTP_STATUS_CANCELLED,
    RTP_STATUS_EXPIRED,
    RTP_STATUS_REJECTED,
    RTP_STATUS_SENT,
    RTP_STATUS_USER_ACCEPTED,
    RTP_STATUS_USER_REJECTED,
    STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_RESPONSE,
    STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_TRANSITION,
    STATUS_UPDATE_ERROR_DESCRIPTION_RTP_NOT_FOUND,
    STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER,
    STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
    STATUS_UPDATE_ERROR_INVALID_RESPONSE,
    STATUS_UPDATE_ERROR_INVALID_TRANSITION,
    STATUS_UPDATE_ERROR_RTP_NOT_FOUND,
    STATUS_UPDATE_ERROR_SERVICE_PROVIDER,
    STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
)
from utils.constants_text_helper import CANCEL_REASON_PAID
from utils.dataset_callback_data_DS_12P_positive_v2 import generate_callback_data_DS_12P_positive_compliant
from utils.dataset_status_update_rtp import generate_status_update_rtp_data
from utils.rtp_status_update_helpers import (
    StatusUpdateRtpContext,
    assert_rtp_deleted_after_status_update,
    assert_status_update_error_response,
    assert_status_update_result,
    update_rtp_status_v2,
    wait_for_rtp_status,
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
    status_update_rtp_factory,
    random_fiscal_code,
    rtp_reader_access_token,
    notice_number,
    expected_reason,
    expected_rtp_status,
):
    context = status_update_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=notice_number,
        expected_final_status=expected_rtp_status,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=200,
        expected_rtp_status=expected_rtp_status,
        expected_reason=expected_reason,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The EPC service provider returns IRNR and the RTP enters ERROR_SEND")
@allure.title("An IRNR status update returns ERROR_SEND and purges the RTP")
@allure.tag("functional", "happy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
def test_status_update_rtp_mock_irnr_error_send_outcome(
    status_update_rtp_factory,
    random_fiscal_code,
    rtp_reader_access_token,
):
    """Verify the public ERROR_SEND outcome represented by IRNR and read-API purge."""
    context = status_update_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=MOCK_STATUS_UPDATE_NOTICE_NUMBER_IRNR,
        expected_final_status=None,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=200,
        expected_rtp_status=None,
        expected_reason="IRNR",
    )
    assert_rtp_deleted_after_status_update(
        reader_token=rtp_reader_access_token,
        resource_id=context.resource_id,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The same successful status update is processed more than once")
@allure.title("Repeating a status update is idempotent")
@allure.tag("functional", "happy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.happy_path
def test_status_update_rtp_mock_is_idempotent(
    status_update_rtp_factory,
    random_fiscal_code,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
):
    context = status_update_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=MOCK_STATUS_UPDATE_NOTICE_NUMBER_ALAC,
        expected_final_status=RTP_STATUS_USER_ACCEPTED,
    )
    repeated_response, repeated_status = update_rtp_status_v2(
        creditor_token=creditor_service_provider_token_a,
        reader_token=rtp_reader_access_token,
        resource_id=context.resource_id,
        expected_final_status=RTP_STATUS_USER_ACCEPTED,
    )

    repeated_context = StatusUpdateRtpContext(
        resource_id=context.resource_id,
        initial_status=context.final_status or context.initial_status,
        final_status=repeated_status,
        status_update_response=repeated_response,
    )
    assert_status_update_result(
        context=repeated_context,
        expected_response_status=200,
        expected_rtp_status=RTP_STATUS_USER_ACCEPTED,
        expected_reason="ALAC",
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The RTP status does not allow the requested transition")
@allure.title("An invalid status transition is rejected")
@allure.tag("functional", "unhappy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_status_update_rtp_mock_rejects_invalid_transition(
    status_update_rtp_resource_factory,
    random_fiscal_code,
    creditor_service_provider_token_a,
    rtp_reader_access_token,
    debtor_sp_mock_cert_key,
):
    created_context = status_update_rtp_resource_factory(
        payer_id=random_fiscal_code,
        notice_number=MOCK_STATUS_UPDATE_NOTICE_NUMBER_ALAC,
    )
    cancel_response = cancel_rtp_v2(
        access_token=creditor_service_provider_token_a,
        resource_id=created_context.resource_id,
        reason=CANCEL_REASON_PAID,
    )
    assert cancel_response.status_code == 204, (
        f"Expected cancellation status 204, got {cancel_response.status_code}: {cancel_response.text}"
    )
    callback_data = generate_callback_data_DS_12P_positive_compliant(
        resource_id=created_context.resource_id,
        original_msg_id=created_context.resource_id.replace("-", ""),
    )
    certificate, key = debtor_sp_mock_cert_key
    callback_response = srtp_rfc_callback_v2(
        cert_path=certificate,
        key_path=key,
        rtp_payload=callback_data,
        include_version_header=False,
    )
    assert callback_response.status_code == 200, (
        f"Expected cancellation callback status 200, got {callback_response.status_code}: {callback_response.text}"
    )
    cancelled_status = wait_for_rtp_status(
        reader_token=rtp_reader_access_token,
        resource_id=created_context.resource_id,
        expected_status=RTP_STATUS_CANCELLED,
    )
    assert cancelled_status == RTP_STATUS_CANCELLED, f"Expected {RTP_STATUS_CANCELLED}, got {cancelled_status}"

    status_update_response, final_status = update_rtp_status_v2(
        creditor_token=creditor_service_provider_token_a,
        reader_token=rtp_reader_access_token,
        resource_id=created_context.resource_id,
        expected_final_status=RTP_STATUS_CANCELLED,
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
        expected_rtp_status=RTP_STATUS_CANCELLED,
        expected_error_code=STATUS_UPDATE_ERROR_INVALID_TRANSITION,
        expected_error_description=STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_TRANSITION,
    )


STATUS_UPDATE_ERROR_SCENARIOS = [
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_400,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-400",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_401,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-401",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_404,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-404",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_406,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-406",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_410,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-410",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_415,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-415",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_422,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-422",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_429,
        422,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER_REJECTION,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER_REJECTION,
        id="provider-429",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_UNKNOWN_REASON,
        422,
        STATUS_UPDATE_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="unknown-reason",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_500,
        500,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-500",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_502,
        500,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-502",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_503,
        500,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-503",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_504,
        500,
        STATUS_UPDATE_ERROR_SERVICE_PROVIDER,
        STATUS_UPDATE_ERROR_DESCRIPTION_SERVICE_PROVIDER,
        id="provider-504",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_EMPTY_BODY,
        422,
        STATUS_UPDATE_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="empty-provider-error-body",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_MALFORMED_REASON,
        422,
        STATUS_UPDATE_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="malformed-reason",
    ),
    pytest.param(
        MOCK_STATUS_UPDATE_NOTICE_NUMBER_TRUNCATED_JSON,
        422,
        STATUS_UPDATE_ERROR_INVALID_RESPONSE,
        STATUS_UPDATE_ERROR_DESCRIPTION_INVALID_RESPONSE,
        id="truncated-json",
    ),
]


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The EPC service provider returns an error or malformed response")
@allure.title("A status-update error is normalized without changing the RTP")
@allure.tag("functional", "unhappy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    "notice_number, expected_response_status, expected_error_code, expected_error_description",
    STATUS_UPDATE_ERROR_SCENARIOS,
)
def test_status_update_rtp_mock_error_scenarios(
    status_update_rtp_factory,
    random_fiscal_code,
    notice_number,
    expected_response_status,
    expected_error_code,
    expected_error_description,
):
    context = status_update_rtp_factory(
        payer_id=random_fiscal_code,
        notice_number=notice_number,
        expected_final_status=RTP_STATUS_SENT,
    )

    assert_status_update_result(
        context=context,
        expected_response_status=expected_response_status,
        expected_rtp_status=RTP_STATUS_SENT,
        expected_error_code=expected_error_code,
        expected_error_description=expected_error_description,
    )


@allure.epic("RTP Send")
@allure.feature("RTP status update")
@allure.story("The requested RTP does not exist")
@allure.title("Requesting a status update for an unknown RTP returns not found")
@allure.tag("functional", "unhappy_path", "rtp_status_update", "mock")
@pytest.mark.send
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_status_update_rtp_unknown_resource(
    creditor_service_provider_token_a,
):
    response = status_update_rtp_v2(
        access_token=creditor_service_provider_token_a,
        status_update_payload=generate_status_update_rtp_data(str(uuid4())),
    )

    assert_status_update_error_response(
        response=response,
        expected_response_status=404,
        expected_error_code=STATUS_UPDATE_ERROR_RTP_NOT_FOUND,
        expected_error_description=STATUS_UPDATE_ERROR_DESCRIPTION_RTP_NOT_FOUND,
    )
