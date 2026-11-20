import uuid

import requests

from api.utils.endpoints import SERVICE_PROVIDERS_REGISTRY_URL
from api.utils.http_utils import HTTP_TIMEOUT


def get_rtp_service_providers(
    access_token: str | None,
    version: str | None,
    *,
    include_request_id: bool = True,
) -> requests.Response:
    return requests.get(
        url=SERVICE_PROVIDERS_REGISTRY_URL,
        headers={
            **({"Authorization": access_token} if access_token is not None else {}),
            **({"Version": version} if version is not None else {}),
            **({"RequestId": str(uuid.uuid4())} if include_request_id else {}),
        },
        timeout=HTTP_TIMEOUT,
    )
