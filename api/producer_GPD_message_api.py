import requests

from api.utils.endpoints import PRODUCER_GPD_MESSAGE_URL
from api.utils.http_utils import APPLICATION_JSON_HEADER
from api.utils.http_utils import HTTP_TIMEOUT

def send_producer_gpd_message(payload: dict, validate: bool = True):

    """Send a message to the GPD queue via the internal API.

    :param payload: The JSON payload for the message.
    :param validate: Whether to enable validation on the API side (default: True).
    :returns: The response from the API call.
    :rtype: requests.Response
    """
    url = PRODUCER_GPD_MESSAGE_URL
    headers = APPLICATION_JSON_HEADER
    return requests.post(url, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
