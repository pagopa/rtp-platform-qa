import allure
import pytest

from api.RTP_get_api import get_rtp
from api.RTP_process_sender import send_gpd_message
from utils.dataset_gpd_message import generate_gpd_message_payload


@allure.epic("RTP GPD Message")
@allure.feature("GPD Message API")
@allure.story("Idempotency of the sender: same Idempotency-Key produces a single DB record")
@allure.title("Two CREATE VALID messages with the same Idempotency-Key both succeed but only one RTP is stored")
@allure.tag("functional", "gpd_message", "rtp_send")
@pytest.mark.send
@pytest.mark.happy_path
def test_send_gpd_message_create_idempotency(
    rtp_consumer_access_token, rtp_reader_access_token, random_fiscal_code, activate_payer
):
    """
    Send the same CREATE VALID message twice.

    Because send_gpd_message derives the Idempotency-Key deterministically from
    the message id (msg_id), reusing the same payload reuses the same key.

    Expectations:
    - Both calls return HTTP 200 (idempotent, not an error).
    - The resourceID in both responses is identical, proving that only one RTP
      record was created in the database.
    - The record is retrievable from the DB via the GET endpoint, confirming
      it was persisted and not just returned from a response cache.
    """

    activate_payer(random_fiscal_code)

    message_payload = generate_gpd_message_payload(fiscal_code=random_fiscal_code, operation="CREATE", status="VALID")

    response_first = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert response_first.status_code == 200, (
        f"First call: expected 200, got {response_first.status_code}. Response: {response_first.text}"
    )

    response_second = send_gpd_message(access_token=rtp_consumer_access_token, message_payload=message_payload)
    assert response_second.status_code == 200, (
        f"Second call: expected 200, got {response_second.status_code}. Response: {response_second.text}"
    )

    body_first = response_first.json()
    body_second = response_second.json()

    assert "resourceID" in body_first, f"Expected 'resourceID' in first response body, got: {response_first.text}"
    assert "resourceID" in body_second, f"Expected 'resourceID' in second response body, got: {response_second.text}"

    resource_id = body_first["resourceID"]

    assert body_second["resourceID"] == resource_id, (
        f"Expected both calls to return the same resourceID (idempotency), "
        f"but got '{resource_id}' and '{body_second['resourceID']}'"
    )

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)
    assert get_response.status_code == 200, (
        f"Expected RTP '{resource_id}' to exist in DB, got {get_response.status_code}: {get_response.text}"
    )
    assert get_response.json()["resourceID"] == resource_id, (
        f"DB record resourceID mismatch: expected '{resource_id}', got '{get_response.json().get('resourceID')}'"
    )
