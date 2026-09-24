import time
from collections.abc import Callable
from dataclasses import dataclass

import requests

from api.RTP_get_api import get_rtp_v2
from api.RTP_send_api import send_rtp_v2, status_update_rtp_v2
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
    creditor_token: str,
    reader_token: str,
    payer_id: str,
    notice_number: str,
    expected_final_status: str | None,
    expected_initial_status: str = RTP_STATUS_SENT,
) -> StatusUpdateRtpContext:
    rtp_data = generate_rtp_data(payer_id=payer_id, notice_number=notice_number)

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
    def is_expected_status(response: requests.Response) -> bool:
        if response.status_code != 200:
            return False

        response_body: JsonType = get_response_body_safe(response)
        assert isinstance(response_body, dict), (
            f"Expected a JSON object while polling RTP {resource_id}, got {response_body!r}. Response: {response.text}"
        )
        return response_body.get("status") == expected_status

    _poll_rtp_response(
        reader_token=reader_token,
        resource_id=resource_id,
        is_ready=is_expected_status,
        expected_outcome=f"reach status {expected_status}",
    )
    return expected_status


def assert_rtp_deleted_after_status_update(
    reader_token: str,
    resource_id: str,
) -> None:
    _poll_rtp_response(
        reader_token=reader_token,
        resource_id=resource_id,
        is_ready=lambda response: response.status_code == 404,
        expected_outcome="be deleted after status update",
    )


def _poll_rtp_response(
    *,
    reader_token: str,
    resource_id: str,
    is_ready: Callable[[requests.Response], bool],
    expected_outcome: str,
) -> requests.Response:
    deadline = time.monotonic() + STATUS_POLL_TIMEOUT_SECONDS
    last_response: requests.Response | None = None

    while time.monotonic() < deadline:
        last_response = get_rtp_v2(access_token=reader_token, rtp_id=resource_id)
        if is_ready(last_response):
            return last_response

        time.sleep(STATUS_POLL_INTERVAL_SECONDS)

    assert last_response is not None, f"No response received while waiting for RTP {resource_id} to {expected_outcome}"
    raise AssertionError(
        f"Expected RTP {resource_id} to {expected_outcome}, but the last response "
        f"was {last_response.status_code}: {last_response.text}"
    )


def assert_status_update_result(
    context: StatusUpdateRtpContext,
    expected_response_status: int,
    expected_rtp_status: str | None,
    expected_reason: str | None = None,
    expected_error_code: str | None = None,
    expected_error_description: str | None = None,
) -> None:
    assert_response_code(
        response=context.status_update_response,
        expected_status=expected_response_status,
        operation="status update",
        expected_rtp_status=context.final_status,
    )
    if expected_rtp_status is not None:
        assert context.final_status == expected_rtp_status, (
            f"Expected RTP status {expected_rtp_status}, got {context.final_status} for resource {context.resource_id}"
        )

    body: JsonType = get_response_body_safe(context.status_update_response)
    assert isinstance(body, dict), (
        f"Expected a JSON object from status update, got {body!r}. Response: {context.status_update_response.text}"
    )

    if expected_response_status == 200:
        assert body.get("resourceId") == context.resource_id, (
            f"Expected response resourceId {context.resource_id}, got {body.get('resourceId')!r}"
        )
        if expected_reason is None:
            assert "reason" not in body, f"Fallback response must omit reason, got {body!r}"
        else:
            assert body.get("reason") == expected_reason, (
                f"Expected response reason {expected_reason}, got {body.get('reason')!r}"
            )
        return

    assert expected_error_code is not None, "Expected an error code for a non-success status update response"
    assert expected_error_description is not None, (
        "Expected an error description for a non-success status update response"
    )
    assert body.get("code") == expected_error_code, (
        f"Expected error code {expected_error_code}, got {body.get('code')!r}. Response: {body!r}"
    )
    assert body.get("description") == expected_error_description, (
        f"Expected error description {expected_error_description!r}, "
        f"got {body.get('description')!r}. Response: {body!r}"
    )


def assert_status_update_error_response(
    response: requests.Response,
    expected_response_status: int,
    expected_error_code: str,
    expected_error_description: str,
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
    assert body.get("code") == expected_error_code, (
        f"Expected error code {expected_error_code}, got {body.get('code')!r}. Response: {body!r}"
    )
    assert body.get("description") == expected_error_description, (
        f"Expected error description {expected_error_description!r}, "
        f"got {body.get('description')!r}. Response: {body!r}"
    )
