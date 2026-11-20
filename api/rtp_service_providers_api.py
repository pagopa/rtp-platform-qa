"""API client module for retrieving versioned RTP Service Providers."""

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
    """Retrieve the list of Technical Service Providers (TSPs) and Service Providers (SPs).

    :param access_token: Bearer authorization token, or None to omit the Authorization header.
    :type access_token: str | None
    :param version: API version header value (e.g. 'v1', 'v2'), or None to omit the Version header.
    :type version: str | None
    :param include_request_id: Whether to include a generated unique RequestId header (defaults to True).
    :type include_request_id: bool
    :return: The HTTP response from the Service Providers Registry endpoint.
    :rtype: requests.Response
    """
    return requests.get(
        url=SERVICE_PROVIDERS_REGISTRY_URL,
        headers={
            **({"Authorization": access_token} if access_token is not None else {}),
            **({"Version": version} if version is not None else {}),
            **({"RequestId": str(uuid.uuid4())} if include_request_id else {}),
        },
        timeout=HTTP_TIMEOUT,
    )
