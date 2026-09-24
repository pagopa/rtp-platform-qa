import time
from dataclasses import dataclass

import requests

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp_v2
from api.RTP_send_api import send_rtp_v2, status_update_rtp_v2
from config.configuration import secrets
from utils.constants_epc_status_update_mock import RTP_STATUS_SENT
from utils.dataset_RTP_data import generate_rtp_data
from utils.dataset_status_update_rtp import generate_status_update_rtp_data
from utils.response_assertions_utils import assert_response_code, get_response_body_safe
from utils.type_utils import JsonType

STATUS_POLL_INTERVAL_SECONDS = 1
STATUS_POLL_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class StatusUpdateRtpContext:
    resource_id: str
    initial_status: str
    final_status: str | None
    status_update_response: requests.Response


def send_and_status_update_rtp_v2(
    debtor_token: str,
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    notice_number: str,
    expected_final_status: str | None,
    service_provider_id: str | None = None,
    expected_initial_status: str = RTP_STATUS_SENT,
) -> StatusUpdateRtpContext:
    if service_provider_id is None:
        service_provider_id = secrets.debtor_service_provider_C.service_provider_id

    rtp_data = generate_rtp_data(payer_id=payer_id, notice_number=notice_number)

    activation_response = activate(
        access_token=debtor_token,
        payer_fiscal_code=rtp_data["payer"]["payerId"],
        service_provider_id=service_provider_id,
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

    initial_status = _wait_for_rtp_status(
        reader_token=reader_token,
        resource_id=resource_id,
        expected_status=expected_initial_status,
    )

    status_update_response = status_update_rtp_v2(
        access_token=creditor_token,
        status_update_payload=generate_status_update_rtp_data(resource_id),
    )

    final_status = (
        _wait_for_rtp_status(
            reader_token=reader_token,
            resource_id=resource_id,
            expected_status=expected_final_status,
        )
        if expected_final_status is not None
        else None
    )

    return StatusUpdateRtpContext(
        resource_id=resource_id,
        initial_status=initial_status,
        final_status=final_status,
        status_update_response=status_update_response,
    )


def _wait_for_rtp_status(
    reader_token: str,
    resource_id: str,
    expected_status: str,
) -> str:
    deadline = time.monotonic() + STATUS_POLL_TIMEOUT_SECONDS
    last_response = None

    while time.monotonic() < deadline:
        last_response = get_rtp_v2(access_token=reader_token, rtp_id=resource_id)
        if last_response.status_code == 200:
            response_body: JsonType = last_response.json()
            if isinstance(response_body, dict) and response_body.get("status") == expected_status:
                return expected_status

        time.sleep(STATUS_POLL_INTERVAL_SECONDS)

    assert last_response is not None
    raise AssertionError(
        f"Expected RTP {resource_id} to reach {expected_status}, but the last response was "
        f"{last_response.status_code}: {last_response.text}"
    )


def assert_rtp_deleted_after_status_update(
    reader_token: str,
    resource_id: str,
) -> None:
    deadline = time.monotonic() + STATUS_POLL_TIMEOUT_SECONDS
    last_response = None

    while time.monotonic() < deadline:
        last_response = get_rtp_v2(access_token=reader_token, rtp_id=resource_id)
        if last_response.status_code == 404:
            return

        time.sleep(STATUS_POLL_INTERVAL_SECONDS)

    assert last_response is not None
    raise AssertionError(
        f"Expected RTP {resource_id} to be deleted after status update, but the last response "
        f"was {last_response.status_code}: {last_response.text}"
    )


def assert_status_update_result(
    context: StatusUpdateRtpContext,
    expected_response_status: int,
    expected_rtp_status: str | None,
    expected_reason: str | None = None,
    expected_error_code: str | None = None,
) -> None:
    assert_response_code(
        response=context.status_update_response,
        expected_status=expected_response_status,
        operation="status update",
        expected_rtp_status=context.final_status,
    )
    if expected_rtp_status is not None:
        assert context.final_status == expected_rtp_status

    body: JsonType = get_response_body_safe(context.status_update_response)
    assert isinstance(body, dict), (
        f"Expected a JSON object from status update, got {body!r}. Response: {context.status_update_response.text}"
    )

    if expected_response_status == 200:
        assert body.get("resourceId") == context.resource_id
        if expected_reason is None:
            assert body.get("reason") is None
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
    assert_response_code(
        response=response,
        expected_status=expected_response_status,
        operation="status update",
        expected_rtp_status="unknown",
    )

    body: JsonType = get_response_body_safe(response)
    assert isinstance(body, dict), (
        f"Expected a JSON error object from status update, got {body!r}. Response: {response.text}"
    )
    assert body.get("code") == expected_error_code
