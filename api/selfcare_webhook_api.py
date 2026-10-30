import uuid

import requests

from api.utils.endpoints import SELFCARE_WEBHOOK_URL
from api.utils.http_utils import HTTP_TIMEOUT


def post_selfcare_webhook(payload: dict, token: str | None, api_key: str | None) -> requests.Response:
    """Send a SelfCare webhook notification. Pass None to omit the Authorization or x-api-key header."""
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Notification-Id": str(uuid.uuid4()),
    }
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if api_key is not None:
        headers["x-api-key"] = api_key

    return requests.post(
        url=SELFCARE_WEBHOOK_URL,
        headers=headers,
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
