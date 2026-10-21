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
    expected_response_code: int | list[int] = 200,
    callback_bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
) -> None:
    """Send the camt.029 cancel status-update callback and check the RTP status.

    Builds one callback body for the given RTP and sends it once per entry in
    ``expected_response_code``, asserting each HTTP response. If
    ``expected_status`` is set, it then waits until the RTP reaches that status.

    Args:
        context: RTP under test. Provides ``resource_id``, the client
            certificate and key used for the callback, and the reader token
            used to poll the RTP status.
        reason_code: EPC cancellation reason (``AEXR``, ``RCAR``, ``RCNR`` or
            ``RCPR``). If ``None``, the ``CxlStsRsnInf`` block is left out of
            the body, so the callback has no reason. The service rejects this
            with 400.
        expected_status: RTP status to wait for after the callbacks. If
            ``None``, no status check is done and the RTP is not polled.
        expected_response_code: Expected HTTP status of the callback. A single
            code sends one callback. A list sends one callback per code, in
            order, which is how repeated calls (such as idempotency checks) are
            tested. Defaults to ``200``.
        callback_bic: BIC of the debtor service provider, placed in
            ``Assgne.Agt`` of the callback body. Defaults to
            ``DEBTOR_SERVICE_PROVIDER_C_ID``.

    Raises:
        AssertionError: If a callback response code does not match the expected
            one, or if the RTP does not reach ``expected_status``.
    """
    calls_array = expected_response_code if isinstance(expected_response_code, list) else [expected_response_code]
    callback_data = StatusUpdateCancelBody.from_resource(
        bic=callback_bic,
        resource_id=context.resource_id,
        reason_code=reason_code,
    )
    for expected_code in calls_array:
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
