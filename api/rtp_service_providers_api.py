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
    headers: dict[str, str] = {}
    if access_token is not None:
        headers["Authorization"] = access_token
    if version is not None:
        headers["Version"] = version
    if include_request_id:
        headers["RequestId"] = str(uuid.uuid4())

    return requests.get(
        url=SERVICE_PROVIDERS_REGISTRY_URL,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
