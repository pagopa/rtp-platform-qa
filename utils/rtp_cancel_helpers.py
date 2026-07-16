"""Helper functions for RTP cancel flows used across functional tests."""

from api.debtor_activation_api import activate
from api.RTP_cancel_api import cancel_rtp_v2
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp_v2
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data


def send_and_cancel_rtp_v2_get_status(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    notice_number: str,
    reason: str,
    expected_cancel_status: int = 204,
    service_provider_id: str | None = None,
) -> str:
    """Activate a debtor, send an RTP via REST API v2 with a forced notice number, cancel it via
    the v2 cancel endpoint, and return the resulting RTP status.

    The forced notice number is used to trigger a specific EPC v4 mock scenario
    (`postRequestToPayCancellationRequest-v4`) on the downstream cancellation call.

    Args:
        debtor_token: ****** for the debtor service provider.
        creditor_token: ****** for the creditor service provider sending/cancelling the RTP.
        reader_token: ****** for the RTP reader.
        payer_id: Fiscal code used as payer ID.
        notice_number: 18-digit notice number forced on the RTP to trigger the EPC mock scenario.
        reason: Cancellation reason. Must be one of: PAID, MODT.
        expected_cancel_status: Expected HTTP status code from the cancel call. Usually 204 (accepted),
            but EPC mock HTTP error scenarios may be synchronously rejected by the PSP with 422.
        service_provider_id: Debtor service provider ID to activate the debtor with. Defaults
            to service provider C (MOCKSP05); pass a different one when the test needs it.

    Returns:
        The RTP status string (e.g. "CANCELLED_ACCR", "CANCELLED_REJECTED", "ERROR_CANCEL", "RFC_SENT").
    """
    if service_provider_id is None:
        service_provider_id = secrets.debtor_service_provider_C.service_provider_id

    rtp_data = generate_rtp_data(payer_id=payer_id, notice_number=notice_number)

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_rtp_v2(access_token=creditor_token, rtp_payload=rtp_data)
    assert send_response.status_code == 201, (
        f"Expected status 201 sending RTP, got {send_response.status_code}. Body: {send_response.text[:200]}"
    )
    assert "Location" in send_response.headers, (
        f"Expected Location header in response but got status {send_response.status_code}. Body: {send_response.text}"
    )
    resource_id = send_response.headers["Location"].split("/")[-1]

    cancel_response = cancel_rtp_v2(creditor_token, resource_id, reason)
    assert cancel_response.status_code == expected_cancel_status, (
        f"Expected status {expected_cancel_status} cancelling RTP, got {cancel_response.status_code}. "
        f"Body: {cancel_response.text[:200]}"
    )

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]
