import requests

from config.configuration import config


def send_rtp(rtp_payload):
    """API to post an rtp request
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        url=config.send_rtp_path,
        json=rtp_payload,
        timeout=config.default_timeout
    )
