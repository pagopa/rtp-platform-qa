import uuid

import requests

from api.utils.api_version import PAYEES_VERSION
from api.utils.endpoints import PAYEES_URL
from api.utils.http_utils import HTTP_TIMEOUT


def get_payee_registry(access_token: str, page: int = 0, size: int = 20):

    return requests.get(
                url=PAYEES_URL,
                headers={
                    'Authorization': access_token,
                    'Version': PAYEES_VERSION,
                    'RequestId': str(uuid.uuid4())
                },
                params={
                    'page': page,
                    'size': size
                },
                timeout=HTTP_TIMEOUT
            )
