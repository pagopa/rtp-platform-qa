import requests

from config.configuration import config

def send_producer_gpd_message(payload: dict, validate: bool = True):
    """Send a message to the GPD queue via the internal API.

    :param payload: The JSON payload for the message.
    :param validate: Whether to enable validation on the API side (default: True).
    :returns: The response from the API call.
    :rtype: requests.Response
    """
    url = f"{config.producer_gpd_message_base_url}/send/gpd/message"
    params = {'validate': 'true' if validate else 'false'}
    headers = {'Content-Type': 'application/json'}
    return requests.post(url, json=payload, headers=headers, timeout=config.default_timeout)
