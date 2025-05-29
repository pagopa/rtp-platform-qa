import uuid

import requests

from config.configuration import config

SERVICE_PROVIDERS_URL = f"{config.rtp_creation_base_url_path}{config.service_providers_registry}"

def get_service_providers_registry(access_token: str):

    return requests.get(
                url=SERVICE_PROVIDERS_URL,
                headers={
                    'Authorization': access_token,
                    'Version': config.service_providers_registry_api_version,
                    'RequestId': str(uuid.uuid4())
                },
                timeout=config.default_timeout
            )
