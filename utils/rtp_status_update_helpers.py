from dataclasses import dataclass

import requests

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp
from api.RTP_send_api import send_rtp_v2, status_update_rtp_v2
from config.configuration import secrets
from utils.constants_epc_status_update_mock import RTP_STATUS_SENT
from utils.dataset_RTP_data import generate_rtp_data
from utils.dataset_status_update_rtp import generate_status_update_rtp_data
from utils.response_assertions_utils import assert_response_code, get_response_body_safe


@dataclass(frozen=True)
class StatusUpdateRtpContext:
    resource_id: str
    initial_status: str
    final_status: str
    status_update_response: requests.Response


def send_and_status_update_rtp_v2(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    notice_number: str,
    service_provider_id: str | None = None,
    expected_initial_status: str = RTP_STATUS_SENT,
) -> StatusUpdateRtpContext:
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
        f"Expected status 201 sending RTP, got {send_response.status_code}. "
        f"Body: {send_response.text[:200]}"
    )
    assert "Location" in send_response.headers, (
        f"Expected Location header in response but got status {send_response.status_code}. "
        f"Body: {send_response.text}"
    )
    resource_id = send_response.headers["Location"].split("/")[-1]

    initial_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert initial_response.status_code == 200, (
        f"Expected status 200 retrieving initial RTP, got {initial_response.status_code}. "
        f"Body: {initial_response.text}"
    )
    initial_status = initial_response.json()["status"]
    assert initial_status == expected_initial_status, (
        f"Expected initial RTP status {expected_initial_status}, got {initial_status}"
    )

    status_update_response = status_update_rtp_v2(
        access_token=creditor_token,
        status_update_payload=generate_status_update_rtp_data(resource_id),
    )

    final_response = get_rtp(access_token=reader_token, rtp_id=resource_id)
    assert final_response.status_code == 200, (
        f"Expected status 200 retrieving final RTP, got {final_response.status_code}. "
        f"Body: {final_response.text}"
    )

    return StatusUpdateRtpContext(
        resource_id=resource_id,
        initial_status=initial_status,
        final_status=final_response.json()["status"],
        status_update_response=status_update_response,
    )


def assert_status_update_result(
    context: StatusUpdateRtpContext,
    expected_response_status: int,
    expected_rtp_status: str,
    expected_reason: str | None = None,
    expected_error_code: str | None = None,
) -> None:
    assert_response_code(
        context.status_update_response,
        expected_response_status,
        "status update",
        context.final_status,
    )
    assert context.final_status == expected_rtp_status

    body = get_response_body_safe(context.status_update_response)
    assert isinstance(body, dict), (
        f"Expected a JSON object from status update, got {body!r}. "
        f"Response: {context.status_update_response.text}"
    )

    if expected_response_status == 200:
        assert body.get("resourceId") == context.resource_id
        if expected_reason is None:
            assert "reason" not in body
        else:
            assert body.get("reason") == expected_reason
        return

    assert expected_error_code is not None
    assert body.get("code") == expected_error_code


def assert_status_update_error_response(
    response: requests.Response,
    expected_response_status: int,
    expected_error_code: str,
) -> None:
    assert_response_code(response, expected_response_status, "status update", "unknown")

    body = get_response_body_safe(response)
    assert isinstance(body, dict), (
        f"Expected a JSON error object from status update, got {body!r}. "
        f"Response: {response.text}"
    )
    assert body.get("code") == expected_error_code
