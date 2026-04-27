"""Helper functions for RTP send flows used across functional tests."""

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data


def send_rtp_and_get_status(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 201,
) -> str:
    """Activate a debtor, send an RTP, and return the resulting RTP status.

    Args:
        debtor_token: Bearer token for the debtor service provider.
        creditor_token: Bearer token for the creditor service provider.
        reader_token: Bearer token for the RTP reader.
        payer_id: Fiscal code used as payer ID (drives mock EPC response).
        expected_send_status: Expected HTTP status code from the send RTP call.

    Returns:
        The RTP status string (e.g. "ACCEPTED", "REJECTED", "SENT").
    """
    rtp_data = generate_rtp_data(payer_id=payer_id)

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_rtp(access_token=creditor_token, rtp_payload=rtp_data)
    assert send_response.status_code == expected_send_status

    resource_id = send_response.headers["Location"].split("/")[-1]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]

# This solution is temporary until we have a more robust way to trigger specific RTP statuses in our mocks.
# In the meantime, this helper can be used in tests that need to verify behavior based on the RTP status after sending (e.g. "ACCEPTED", "REJECTED", "SENT")
# by using specific payer IDs that drive the mock EPC response to return the desired status.
def send_rtp_and_get_status_rejected(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP, and return the resulting RTP status.

    Args:
        debtor_token: Bearer token for the debtor service provider.
        creditor_token: Bearer token for the creditor service provider.
        reader_token: Bearer token for the RTP reader.
        payer_id: Fiscal code used as payer ID (drives mock EPC response).
        expected_send_status: Expected HTTP status code from the send RTP call.

    Returns:
        The RTP status string (e.g. "ACCEPTED", "REJECTED", "SENT").
    """
    assert expected_send_status >= 400, "This helper is intended for cases where the send RTP call is expected to fail (e.g. REJECTED status), please use send_rtp_and_get_status for cases where the send is expected to succeed."
    rtp_data = generate_rtp_data(payer_id=payer_id)
    notice_number = rtp_data["paymentNotice"]["noticeNumber"]

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_rtp(access_token=creditor_token, rtp_payload=rtp_data)
    assert send_response.status_code == expected_send_status

    resource_id = send_response.headers["Location"].split("/")[-1]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]
