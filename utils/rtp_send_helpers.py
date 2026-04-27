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

    status = get_status_from_notice_number(notice_number)

    return get_response.json()["status"]

def get_status_from_notice_number(notice_number: str) -> str:
    """Helper function to retrieve the RTP status by notice number.

    This is a workaround for cases where the send RTP call is expected to fail (e.g. REJECTED status) and thus we cannot retrieve the RTP ID from the Location header to check the status via the get RTP endpoint.

    Args:
        notice_number: The notice number of the payment notice included in the RTP payload.
    Returns:
        The RTP status string (e.g. "ACCEPTED", "REJECTED", "SENT").
    """
    # In the current mock setup, the notice number is unique for each send RTP call and can be used to correlate the get RTP response to the original send RTP request.
    # This allows us to retrieve the RTP status even in cases where the send RTP call fails and we cannot get the RTP ID from the Location header.
    response = get_rtp_by_notice_number(notice_number)
    assert response.status_code == 200, "Error retrieving RTP by notice number"
    return response.json()[-1]["status"]

def get_rtp_by_notice_number(notice_number: str) -> List[dict]:
    """Helper function to retrieve the RTP details by notice number.

    Args:
        notice_number: The notice number of the payment notice included in the RTP payload.

    Returns:
        The response object from the get RTP API call.
    """
    # TODO: COMPLETE THIS METHOD AND FIX THE ABOVE ONES.
    pass
