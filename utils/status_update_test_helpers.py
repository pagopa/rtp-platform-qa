from collections.abc import Mapping

from api.RTP_callback_api import srtp_status_update_callback
from api.RTP_get_api import get_rtp_v2
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_status_update_callback import generate_status_update_callback_data
from utils.response_assertions_utils import assert_response_code
from utils.status_update_test_context import StatusUpdateRtpContext


def assert_status_update_transition(
    context: StatusUpdateRtpContext,
    reason_code: str | None,
    expected_status: str,
    expected_response_code: int = 200,
    extra_headers: Mapping[str, str] | None = None,
    callback_bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    expected_resource_response_code: int = 200,
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

    get_response = get_rtp_v2(
        access_token=context.reader_access_token,
        rtp_id=context.resource_id,
    )
    assert_response_code(
        get_response,
        expected_resource_response_code,
        "GET RTP",
        expected_status,
    )
    if expected_resource_response_code == 200:
        assert get_response.json()["status"] == expected_status, (
            f"Expected RTP status {expected_status}, got {get_response.json()['status']}"
        )
