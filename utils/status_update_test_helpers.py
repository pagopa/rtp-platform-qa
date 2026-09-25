from collections.abc import Mapping

from api.RTP_callback_api import srtp_status_update_callback
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_status_update_callback import generate_status_update_callback_data
from utils.response_assertions_utils import assert_response_code
from utils.rtp_status_update_helpers import assert_rtp_deleted_after_status_update, wait_for_rtp_status
from utils.status_update_test_context import StatusUpdateRtpContext


def assert_status_update_transition(
    context: StatusUpdateRtpContext,
    reason_code: str | None,
    expected_status: str,
    expected_response_code: int = 200,
    extra_headers: Mapping[str, str] | None = None,
    callback_bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    resource_should_be_deleted: bool = False,
) -> None:
    callback_data = generate_status_update_callback_data(
        bic=callback_bic,
        resource_id=context.resource_id,
        original_msg_id=context.resource_id,
        reason_code=reason_code,
    )
    callback_response = srtp_status_update_callback(
        rtp_payload=callback_data,
        cert_path=context.certificate,
        key_path=context.key,
        extra_headers=extra_headers,
    )
    assert_response_code(
        callback_response,
        expected_response_code,
        "status-update callback",
        reason_code or "missing reason code",
    )

    if resource_should_be_deleted:
        assert_rtp_deleted_after_status_update(
            reader_token=context.reader_access_token,
            resource_id=context.resource_id,
        )
        return

    wait_for_rtp_status(
        reader_token=context.reader_access_token,
        resource_id=context.resource_id,
        expected_status=expected_status,
    )
