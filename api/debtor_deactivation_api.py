import uuid

import requests

from api.utils.api_version import DEACTIVATION_VERSION
from api.utils.endpoints import DEACTIVATION_URL
from api.utils.http_utils import HTTP_TIMEOUT


def deactivate(access_token: str, activation_id: str):
    """API to deactivate a debtor
        :param access_token: JWT access token
        :param activation_id: ID of the activation to delete
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.delete(
        url=f"{DEACTIVATION_URL}/{activation_id}",
        headers={
            'Authorization': f'{access_token}',
            'Version': DEACTIVATION_VERSION,
            'RequestId': str(uuid.uuid4())
        },
        timeout=HTTP_TIMEOUT
    )
