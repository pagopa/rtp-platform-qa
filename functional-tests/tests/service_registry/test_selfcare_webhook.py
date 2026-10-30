import allure
import pytest

from api.selfcare_webhook_api import post_selfcare_webhook
from config.configuration import secrets
from utils.dataset_selfcare_webhook_data import (
    generate_selfcare_delegation_created_payload,
    generate_selfcare_delegation_deleted_payload,
)

INVALID_API_KEY = "11111111111111111"
INVALID_TOKEN = "not-a-jwt-valid"


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
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


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
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


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
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


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
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
