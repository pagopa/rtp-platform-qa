import uuid

import allure
import pytest
from requests import Response

from api.selfcare_webhook_api import post_selfcare_webhook
from config.configuration import secrets
from utils.dataset_selfcare_webhook_data import (
    SELFCARE_NOTIFICATION_ID,
    generate_selfcare_delegation_created_payload,
    generate_selfcare_delegation_deleted_payload,
)

INVALID_API_KEY = "11111111111111111"
INVALID_TOKEN = "not-a-jwt-valid"

INVALID_API_KEY_MESSAGE = "A valid subscription key is required in the x-api-key header."
INVALID_TOKEN_MESSAGE = "Unauthorized: Invalid JWT token"
NOTIFICATION_ID_MISMATCH_MESSAGE = "X-Webhook-Notification-Id header does not match JWT notification_id claim"


def assert_unauthorized(response: Response, expected_message: str) -> None:
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    body = response.json()
    assert body.get("statusCode") == 401, f"Unexpected error body: {body}"
    assert body.get("message") == expected_message, f"Unexpected error body: {body}"


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation created notification returns 200")
@allure.tag("functional", "happy_path", "selfcare_webhook")
@pytest.mark.happy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_delegation_created() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation deleted notification returns 200")
@allure.tag("functional", "happy_path", "selfcare_webhook")
@pytest.mark.happy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_delegation_deleted() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_deleted_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification without x-api-key returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_missing_api_key() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=None,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert_unauthorized(response, INVALID_API_KEY_MESSAGE)


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification with invalid x-api-key returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_invalid_api_key() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=INVALID_API_KEY,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert_unauthorized(response, INVALID_API_KEY_MESSAGE)


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification without authorization returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_missing_authorization() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=None,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert_unauthorized(response, INVALID_TOKEN_MESSAGE)


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification with invalid token returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_invalid_token() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=INVALID_TOKEN,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=SELFCARE_NOTIFICATION_ID,
    )

    assert_unauthorized(response, INVALID_TOKEN_MESSAGE)


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification without X-Webhook-Notification-Id returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_missing_notification_id() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=None,
    )

    assert_unauthorized(response, NOTIFICATION_ID_MISMATCH_MESSAGE)


@allure.epic("Service Registry Payees")
@allure.feature("SelfCare Webhook")
@allure.story("SelfCare notifies rtp-payees of delegation changes")
@allure.title("Delegation notification with mismatching X-Webhook-Notification-Id returns 401")
@allure.tag("functional", "unhappy_path", "selfcare_webhook")
@pytest.mark.unhappy_path
@pytest.mark.selfcare_webhook
def test_selfcare_webhook_invalid_notification_id() -> None:
    response = post_selfcare_webhook(
        payload=generate_selfcare_delegation_created_payload(),
        token=secrets.selfcare_webhook.token,
        api_key=secrets.selfcare_webhook.api_key,
        notification_id=str(uuid.uuid4()),
    )

    assert_unauthorized(response, NOTIFICATION_ID_MISMATCH_MESSAGE)
