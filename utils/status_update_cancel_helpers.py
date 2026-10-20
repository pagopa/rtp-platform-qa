from api.RTP_callback_api import srtp_status_update_cancel_callback
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.response_assertions_utils import assert_response_code
from utils.rtp_status_update_helpers import wait_for_rtp_status
from utils.status_update_cancel_body import StatusUpdateCancelBody
from utils.status_update_test_context import StatusUpdateRtpContext


def assert_status_update_cancel_transition(
    context: StatusUpdateRtpContext,
    reason_code: str | None,
    expected_status: str | None,
    expected_response_code: int | dict[int, int] = 200,
    callback_bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    number_of_calls: int = 1,
) -> None:
    callback_data = StatusUpdateCancelBody.from_resource(
        bic=callback_bic,
        resource_id=context.resource_id,
        reason_code=reason_code,
    )
    for i in range(number_of_calls):
        expected_code = expected_response_code[i] if isinstance(expected_response_code, dict) else expected_response_code
        callback_response = srtp_status_update_cancel_callback(
            rtp_payload=callback_data.to_dict(),
            cert_path=context.certificate,
            key_path=context.key,
        )
        assert_response_code(
            callback_response,
            expected_code,
            "cancel callback (camt.029)",
            reason_code or "missing reason code",
        )
    if expected_status is not None:
        wait_for_rtp_status(
            reader_token=context.reader_access_token,
            resource_id=context.resource_id,
            expected_status=expected_status,
        )
