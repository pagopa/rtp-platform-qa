"""Helper functions for RTP send flows used across functional tests."""

from collections.abc import Callable

import requests

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp
from api.RTP_get_api import get_rtp_by_notice_number as api_get_rtp_by_notice_number
from api.RTP_process_sender import send_gpd_message
from api.RTP_send_api import send_rtp, send_rtp_v2
from config.configuration import secrets
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.dataset_RTP_data import generate_rtp_data


def send_rtp_and_get_status(
    debtor_token: str,
    rtp_consumer_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 200,
) -> str:
    """Activate a debtor, send an RTP via GPD message, and return the resulting RTP status.

    Args:
        debtor_token: ****** for the debtor service provider.
        rtp_consumer_token: ****** for the RTP consumer (GPD message sender).
        reader_token: ****** for the RTP reader.
        payer_id: Fiscal code used as payer ID (drives mock EPC response).
        expected_send_status: Expected HTTP status code from the send GPD message call.

    Returns:
        The RTP status string (e.g. "ACCEPTED", "REJECTED", "SENT").
    """
    message_payload = generate_gpd_message_payload(fiscal_code=payer_id, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_token,
        payer_id,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_token, message_payload=message_payload)
    assert send_response.status_code == expected_send_status

    resource_id = send_response.json()["resourceId"]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]


def send_rtp_and_get_status_by_notice_number(
    debtor_token: str,
    rtp_consumer_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via GPD message expecting a synchronous rejection (422),
    then retrieve the RTP status by notice number (nav field).

    Used for RJCT scenarios where the EPC synchronously rejects and the server returns 422.
    """
    message_payload = generate_gpd_message_payload(fiscal_code=payer_id, operation="CREATE", status="VALID")
    notice_number = message_payload["nav"]

    activation_response = activate(
        debtor_token,
        payer_id,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_token, message_payload=message_payload)
    assert send_response.status_code == expected_send_status

    return get_status_from_notice_number(reader_token, notice_number)


def get_status_from_notice_number(access_token: str, notice_number: str) -> str:
    rtp_data = get_rtp_by_notice_number(access_token, notice_number)
    return rtp_data["status"]


def get_rtp_by_notice_number(access_token: str, notice_number: str) -> dict:
    response = api_get_rtp_by_notice_number(access_token, notice_number)
    assert response.status_code == 200, f"Error retrieving RTP by notice number. Status Code: {response.status_code}"

    payload = response.json()
    assert isinstance(payload, list) and payload, (
        f"Expected non-empty list when retrieving RTP by notice number {notice_number}. Response body: {response.text}"
    )

    return payload[-1]


def _send_rtp_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    send_fn: Callable[[str, dict], requests.Response],
    expected_send_status: int = 201,
) -> str:
    """Internal helper: activate a debtor, send an RTP via REST and return the resulting status."""
    rtp_data = generate_rtp_data(payer_id=payer_id)

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_fn(creditor_token, rtp_data)
    assert send_response.status_code == expected_send_status, (
        f"Expected status {expected_send_status}, got {send_response.status_code}. Body: {send_response.text[:200]}"
    )

    assert "Location" in send_response.headers, (
        f"Expected Location header in response but got status {send_response.status_code}. "
        f"Body: {send_response.text}"
    )
    resource_id = send_response.headers["Location"].split("/")[-1]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]


def _send_rtp_by_notice_number_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    send_fn: Callable[[str, dict], requests.Response],
    expected_send_status: int = 422,
) -> str:
    """Internal helper: activate a debtor, send an RTP via REST expecting RJCT and return status by notice number."""
    rtp_data = generate_rtp_data(payer_id=payer_id)
    notice_number = rtp_data["paymentNotice"]["noticeNumber"]

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_fn(creditor_token, rtp_data)
    assert send_response.status_code == expected_send_status, (
        f"Expected status {expected_send_status}, got {send_response.status_code}. Body: {send_response.text[:200]}"
    )

    return get_status_from_notice_number(reader_token, notice_number)


def send_rtp_and_get_status_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 201,
) -> str:
    """Activate a debtor, send an RTP via REST API (/rtps), and return the resulting RTP status.

    Used for _THROUGH_WEB_API test variants that exercise the legacy REST send endpoint.
    """
    return _send_rtp_via_rest(
        debtor_token, creditor_token, reader_token, payer_id,
        lambda token, payload: send_rtp(access_token=token, rtp_payload=payload),
        expected_send_status,
    )


def send_rtp_and_get_status_by_notice_number_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via REST API expecting a synchronous RJCT (422),
    then retrieve the RTP status by notice number.

    Used for _THROUGH_WEB_API RJCT test variants.
    """
    return _send_rtp_by_notice_number_via_rest(
        debtor_token, creditor_token, reader_token, payer_id,
        lambda token, payload: send_rtp(access_token=token, rtp_payload=payload),
        expected_send_status,
    )


def send_rtp_v2_and_get_status_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 201,
) -> str:
    """Activate a debtor, send an RTP via REST API v2 (/rtps with Version: v2), and return the resulting RTP status."""
    return _send_rtp_via_rest(
        debtor_token, creditor_token, reader_token, payer_id,
        lambda token, payload: send_rtp_v2(access_token=token, rtp_payload=payload),
        expected_send_status,
    )


def send_rtp_v2_and_get_status_by_notice_number_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via REST API v2 expecting a synchronous RJCT (422),
    then retrieve the RTP status by notice number.
    """
    return _send_rtp_by_notice_number_via_rest(
        debtor_token, creditor_token, reader_token, payer_id,
        lambda token, payload: send_rtp_v2(access_token=token, rtp_payload=payload),
        expected_send_status,
    )



def send_rtp_and_get_status(
    debtor_token: str,
    rtp_consumer_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 200,
) -> str:
    """Activate a debtor, send an RTP via GPD message, and return the resulting RTP status.

    Args:
        debtor_token: Bearer token for the debtor service provider.
        rtp_consumer_token: Bearer token for the RTP consumer (GPD message sender).
        reader_token: Bearer token for the RTP reader.
        payer_id: Fiscal code used as payer ID (drives mock EPC response).
        expected_send_status: Expected HTTP status code from the send GPD message call.

    Returns:
        The RTP status string (e.g. "ACCEPTED", "REJECTED", "SENT").
    """
    message_payload = generate_gpd_message_payload(fiscal_code=payer_id, operation="CREATE", status="VALID")

    activation_response = activate(
        debtor_token,
        payer_id,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_token, message_payload=message_payload)
    assert send_response.status_code == expected_send_status

    resource_id = send_response.json()["resourceId"]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]


def send_rtp_and_get_status_by_notice_number(
    debtor_token: str,
    rtp_consumer_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via GPD message expecting a synchronous rejection (422),
    then retrieve the RTP status by notice number (nav field).

    Used for RJCT scenarios where the EPC synchronously rejects and the server returns 422.
    """
    message_payload = generate_gpd_message_payload(fiscal_code=payer_id, operation="CREATE", status="VALID")
    notice_number = message_payload["nav"]

    activation_response = activate(
        debtor_token,
        payer_id,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_gpd_message(access_token=rtp_consumer_token, message_payload=message_payload)
    assert send_response.status_code == expected_send_status

    return get_status_from_notice_number(reader_token, notice_number)


def get_status_from_notice_number(access_token: str, notice_number: str) -> str:
    rtp_data = get_rtp_by_notice_number(access_token, notice_number)
    return rtp_data["status"]


def get_rtp_by_notice_number(access_token: str, notice_number: str) -> dict:
    response = api_get_rtp_by_notice_number(access_token, notice_number)
    assert response.status_code == 200, f"Error retrieving RTP by notice number. Status Code: {response.status_code}"

    payload = response.json()
    assert isinstance(payload, list) and payload, (
        f"Expected non-empty list when retrieving RTP by notice number {notice_number}. Response body: {response.text}"
    )

    return payload[-1]


def send_rtp_and_get_status_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 201,
) -> str:
    """Activate a debtor, send an RTP via REST API (/rtps), and return the resulting RTP status.

    Used for _THROUGH_WEB_API test variants that exercise the legacy REST send endpoint.
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


def send_rtp_and_get_status_by_notice_number_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via REST API expecting a synchronous RJCT (422),
    then retrieve the RTP status by notice number.

    Used for _THROUGH_WEB_API RJCT test variants.
    """
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

    return get_status_from_notice_number(reader_token, notice_number)


def send_rtp_v2_and_get_status_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 201,
) -> str:
    """Activate a debtor, send an RTP via REST API v2 (/rtps with Version: v2), and return the resulting RTP status."""
    rtp_data = generate_rtp_data(payer_id=payer_id)

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_rtp_v2(access_token=creditor_token, rtp_payload=rtp_data)
    assert send_response.status_code == expected_send_status

    resource_id = send_response.headers["Location"].split("/")[-1]

    get_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert get_response.status_code == 200

    return get_response.json()["status"]


def send_rtp_v2_and_get_status_by_notice_number_via_rest(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    expected_send_status: int = 422,
) -> str:
    """Activate a debtor, send an RTP via REST API v2 expecting a synchronous RJCT (422),
    then retrieve the RTP status by notice number.
    """
    rtp_data = generate_rtp_data(payer_id=payer_id)
    notice_number = rtp_data["paymentNotice"]["noticeNumber"]

    activation_response = activate(
        debtor_token,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code in (201, 409), "Error activating debtor"

    send_response = send_rtp_v2(access_token=creditor_token, rtp_payload=rtp_data)
    assert send_response.status_code == expected_send_status

    return get_status_from_notice_number(reader_token, notice_number)
