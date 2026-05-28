"""Helper functions for RTP send flows used across functional tests."""

import time

from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload
from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp
from api.RTP_get_api import get_rtp_by_notice_number as api_get_rtp_by_notice_number
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


def send_rtp_and_get_status_by_notice_number(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    assert expected_send_status >= 400

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

    status = get_status_from_notice_number(reader_token, notice_number)

    return status

def send_rtp_and_get_status_by_notice_number_mock_only(
    rtp_consumer_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Send a GPD message and return the resulting RTP status by notice number.

    Intended for mock-only scenarios where the payer fiscal code is pre-configured
    in the mock EPC to trigger a specific synchronous RJCT response (e.g. with extra
    fields or missing _links). Uses the GPD message flow instead of the direct RTP
    send flow, so no debtor activation is required.

    Args:
        rtp_consumer_token: Bearer token for the RTP consumer (GPD message sender).
        reader_token: Bearer token for the RTP reader.
        payer_id: Fiscal code used as payer ID (drives the mock EPC response).
        expected_send_status: Expected HTTP status code from the GPD message call (must be >= 400).

    Returns:
        The RTP status string (e.g. "REJECTED").
    """
    assert expected_send_status >= 400

    message_payload = generate_gpd_message_payload(fiscal_code=payer_id, operation="CREATE", status="VALID")
    notice_number = message_payload["nav"]

    response = send_gpd_message(access_token=rtp_consumer_token, message_payload=message_payload)
    assert response.status_code == expected_send_status

    status = get_status_from_notice_number(reader_token, notice_number)

    return status


def get_status_from_notice_number(access_token: str, notice_number: str) -> str:
    rtp_data = get_rtp_by_notice_number(access_token, notice_number)
    return rtp_data["status"]


def get_rtp_by_notice_number(access_token: str, notice_number: str) -> dict:

    response = api_get_rtp_by_notice_number(access_token, notice_number)
    assert response.status_code == 200, f"Error retrieving RTP by notice number. Status Code: {response.status_code}"

    payload = response.json()
    assert isinstance(payload, list) and payload, (
        f"Expected non-empty list when retrieving RTP by notice number {notice_number}. "
        f"Response body: {response.text}"
    )

    return payload[-1]
