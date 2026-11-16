import uuid

import requests

from api.utils.endpoints import RTP_SERVICE_PROVIDERS_URL
from api.utils.http_utils import HTTP_TIMEOUT


def get_rtp_service_providers(access_token: str, version: str) -> requests.Response:
    return requests.get(
        url=RTP_SERVICE_PROVIDERS_URL,
        headers={"Authorization": access_token, "Version": version, "RequestId": str(uuid.uuid4())},
        timeout=HTTP_TIMEOUT,
    )
