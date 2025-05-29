import uuid

import requests

from config.configuration import config

ACTIVATION_URL = config.activation_base_url_path + config.activation_path


def deactivate(access_token: str, activation_id: str):
    """API to deactivate a debtor
        :param access_token: JWT access token
        :param activation_id: ID of the activation to delete
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.delete(
        url=f"{ACTIVATION_URL}/{activation_id}",
        headers={
            'Authorization': f'{access_token}',
            'Version': 'v1',
            'RequestId': str(uuid.uuid4())
        },
        timeout=config.default_timeout
    )
