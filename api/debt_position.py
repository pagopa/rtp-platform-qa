import uuid

import requests

from config.configuration import config
import requests


DEBT_POSITIONS_URL = config.debt_positions_base_url_path + config.debt_positions_path
DEBT_POSITIONS_DEV_URL = (
    config.debt_positions_dev_base_url_path + config.debt_positions_dev_path
)

GET_BY_NOTICE_NUMBER_URL = (
    config.rtp_creation_base_url_path.rstrip("/")
    + "/"
    + config.send_rtp_path.lstrip("/")
)

print(f"GET_BY_NOTICE_NUMBER_URL: {GET_BY_NOTICE_NUMBER_URL}")


def create_debt_position(
    subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True
) -> requests.Response:
    """API to create a debt position and optionally publish it."""
    return requests.post(
        url=DEBT_POSITIONS_URL.format(organizationId=organization_id),
        headers={
            "ocp-apim-subscription-key": subscription_key,
            "Content-Type": "application/json",
        },
        params={"toPublish": to_publish},
        json=payload,
        timeout=config.default_timeout,
    )


def create_debt_position_dev(
    subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True
) -> requests.Response:
    """API to create a debt position in DEV environment and optionally publish it."""
    return requests.post(
        url=DEBT_POSITIONS_DEV_URL.format(organizationId=organization_id),
        headers={
            "ocp-apim-subscription-key": subscription_key,
            "Content-Type": "application/json",
        },
        params={"toPublish": to_publish},
        json=payload,
        timeout=config.default_timeout,
    )


def get_debt_positions_by_notice_number(
    notice_number: str, access_token: str
) -> requests.Response:
    """
    Retrieve RTPs via noticeNumber (iuv), chiamando esattamente:
      GET https://api-rtp.uat.cstar.pagopa.it/rtp/rtps?noticeNumber=…
    """
    base = config.rtp_creation_base_url_path.rstrip("/")
    path = config.send_rtp_path.lstrip("/")
    url = f"{base}/{path}?noticeNumber={notice_number}"

    auth_header = (
        access_token if access_token.startswith("Bearer ") else f"Bearer {access_token}"
    )
    headers = {
        "Version": "v1",
        "RequestId": str(uuid.uuid4()),
        "Authorization": auth_header,
    }

    print(f"[DEBUG] GET URL:    {url}")
    print(f"[DEBUG] HEADERS:    {headers}")

    response = requests.get(url, headers=headers, timeout=config.default_timeout)

    print(f"[DEBUG] STATUS:     {response.status_code}")
    allow = response.headers.get("Allow")
    if allow is not None:
        print(f"[DEBUG] ALLOW:      {allow}")
    try:
        print(f"[DEBUG] BODY:       {response.json()}")
    except ValueError:
        print(f"[DEBUG] BODY TEXT:  {response.text}")

    return response
