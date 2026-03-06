import re
import time

import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp_delivery_status
from api.RTP_process_sender import send_gpd_message
from config.configuration import secrets
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.fiscal_code_utils import fake_fc
from utils.generators_utils import generate_notice_number, generate_random_organization_id

_SEND_PROCESSING_WAIT_S = 5

_STATUS_DELIVERED = "PD_RTP_DELIVERED"
_STATUS_NOT_DELIVERED = "PD_RTP_NOT_DELIVERED"

_PROCESSING_DATE_RE = re.compile(r"^((?:(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2}(?:\.\d+)?))(Z|[\+-]\d{2}:\d{2})?)$")


@allure.epic("RTP Get")
@allure.feature("RTP Delivery Status")
@allure.story("Payee checks whether an RTP was delivered")
@allure.title("GPD message sent → RTP SENT → PD_RTP_DELIVERED with processingDate")
@allure.tag("functional", "happy_path", "get", "rtp_get")
@pytest.mark.get
@pytest.mark.happy_path
def test_get_delivery_status_sent_rtp(
    debtor_service_provider_token_a: str,
    rtp_consumer_access_token: str,
) -> None:
    """
    Given a debtor is activated and a GPD message (CREATE) is sent via POST /gpd/message,
    when the rtp-sender processes it and the RTP reaches status SENT,
    when the payee queries the delivery-status endpoint with the correct noticeNumber
    (nav) and payeeId (ec_tax_code),
    then the response body must contain status=PD_RTP_DELIVERED, a non-null processingDate
    in ISO 8601 format, and processingDate must match the SEND_RTP event timestamp from
    the GPD message response (truncated to millisecond precision).
    """
    fiscal_code: str = fake_fc()

    activation_response = activate(
        debtor_service_provider_token_a,
        fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, (
        f"Debtor activation failed: {activation_response.status_code} {activation_response.text}"
    )

    message_payload = generate_gpd_message_payload(fiscal_code, "CREATE")

    send_response = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload,
    )
    assert send_response.status_code == 200, (
        f"GPD message send failed: {send_response.status_code} {send_response.text}"
    )

    time.sleep(_SEND_PROCESSING_WAIT_S)

    delivery_response = get_rtp_delivery_status(
        access_token=debtor_service_provider_token_a,
        notice_number=message_payload["nav"],
        payee_id=message_payload["ec_tax_code"],
    )

    assert delivery_response.status_code == 200, (
        f"Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}"
    )

    body = delivery_response.json()

    assert body.get("status") == _STATUS_DELIVERED, (
        f"Expected status='{_STATUS_DELIVERED}', got status='{body.get('status')}'"
    )

    processing_date_str: str = body.get("processingDate")
    assert processing_date_str is not None, "Expected 'processingDate' to be non-null for a delivered RTP"
    assert _PROCESSING_DATE_RE.match(processing_date_str), (
        f"'processingDate' does not match ISO 8601 format: '{processing_date_str}'"
    )

    send_rtp_event = next(
        (e for e in send_response.json().get("events", []) if e.get("triggerEvent") == "SEND_RTP"),
        None,
    )
    assert send_rtp_event is not None, "No SEND_RTP event found in the gpd message response events"

    event_ts_ms = re.sub(r"(\.\d{3})\d*", r"\1", send_rtp_event["timestamp"])
    assert processing_date_str == event_ts_ms, (
        f"'processingDate' {processing_date_str!r} does not match "
        f"SEND_RTP event timestamp {send_rtp_event['timestamp']!r}"
    )


@allure.epic("RTP Get")
@allure.feature("RTP Delivery Status")
@allure.story("Payee checks whether an RTP was delivered")
@allure.title("Non-existent noticeNumber → PD_RTP_NOT_DELIVERED")
@allure.tag("functional", "unhappy_path", "get", "rtp_get")
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_delivery_status_notice_number_not_found(
    debtor_service_provider_token_a: str,
) -> None:
    """
    Given a noticeNumber that does not correspond to any RTP in the database,
    when the payee queries the delivery-status endpoint,
    then the response must be HTTP 200 with status=PD_RTP_NOT_DELIVERED and
    processingDate absent or null.
    """
    delivery_response = get_rtp_delivery_status(
        access_token=debtor_service_provider_token_a,
        notice_number=generate_notice_number(),
        payee_id=generate_random_organization_id(),
    )

    assert delivery_response.status_code == 200, (
        f"Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}"
    )

    body = delivery_response.json()
    assert set(body.keys()) <= {"status", "processingDate"}, (
        f"Unexpected fields in response: {set(body.keys()) - {'status', 'processingDate'}}"
    )

    assert body.get("status") == _STATUS_NOT_DELIVERED, (
        f"Expected status='{_STATUS_NOT_DELIVERED}', got status='{body.get('status')}'"
    )
    assert body.get("processingDate") is None, (
        f"Expected 'processingDate' to be null or absent, got '{body.get('processingDate')}'"
    )


@allure.epic("RTP Get")
@allure.feature("RTP Delivery Status")
@allure.story("Payee checks whether an RTP was delivered")
@allure.title("Existing noticeNumber with wrong payeeId → PD_RTP_NOT_DELIVERED")
@allure.tag("functional", "unhappy_path", "get", "rtp_get")
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_delivery_status_wrong_payee_id(
    debtor_service_provider_token_a: str,
    rtp_consumer_access_token: str,
) -> None:
    """
    Given an RTP is sent successfully (status SENT) for a given noticeNumber + payeeId,
    when the payee queries the delivery-status endpoint with the correct noticeNumber
    but a different payeeId,
    then the response must be HTTP 200 with status=PD_RTP_NOT_DELIVERED, verifying
    that the endpoint filters on both fields.
    """
    fiscal_code: str = fake_fc()

    activation_response = activate(
        debtor_service_provider_token_a,
        fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, (
        f"Debtor activation failed: {activation_response.status_code} {activation_response.text}"
    )

    message_payload = generate_gpd_message_payload(fiscal_code, "CREATE")

    send_response = send_gpd_message(
        access_token=rtp_consumer_access_token,
        message_payload=message_payload,
    )
    assert send_response.status_code == 200, (
        f"GPD message send failed: {send_response.status_code} {send_response.text}"
    )

    time.sleep(_SEND_PROCESSING_WAIT_S)

    delivery_response = get_rtp_delivery_status(
        access_token=debtor_service_provider_token_a,
        notice_number=message_payload["nav"],
        payee_id=generate_random_organization_id(),
    )

    assert delivery_response.status_code == 200, (
        f"Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}"
    )

    body = delivery_response.json()
    assert set(body.keys()) <= {"status", "processingDate"}, (
        f"Unexpected fields in response: {set(body.keys()) - {'status', 'processingDate'}}"
    )

    assert body.get("status") == _STATUS_NOT_DELIVERED, (
        f"Expected status='{_STATUS_NOT_DELIVERED}', got status='{body.get('status')}'"
    )
    assert body.get("processingDate") is None, (
        f"Expected 'processingDate' to be null or absent, got '{body.get('processingDate')}'"
    )
