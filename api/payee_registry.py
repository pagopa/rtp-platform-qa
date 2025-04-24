import uuid

import requests

from config.configuration import config

PAYEES_URL = f"{config.rtp_creation_base_url_path}{config.payees_registry_path}"

def get_payee_registry(access_token: str, page: int = 0, size: int = 20):

    return requests.get(
                url=PAYEES_URL,
                headers={
                    'Authorization': access_token,
                    'Version': config.payees_registry_api_version,
                    'RequestId': str(uuid.uuid4())
                },
                params={
                    'page': page,
                    'size': size
                },
                timeout=config.default_timeout
            )
