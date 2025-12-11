import uuid

import requests

from api.utils.api_version import SERVICE_PROVIDER_VERSION
from api.utils.endpoints import SERVICE_PROVIDERS_URL
from api.utils.http_utils import HTTP_TIMEOUT



def get_service_providers_registry(access_token: str):

    return requests.get(
                url=SERVICE_PROVIDERS_URL,
                headers={
                    'Authorization': access_token,
                    'Version': SERVICE_PROVIDER_VERSION,
                    'RequestId': str(uuid.uuid4())
                },
                timeout=HTTP_TIMEOUT
            )
