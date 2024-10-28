import requests

from config.configuration import config


def landing_page():
    """API to get landing page
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.get(
        url=config.landing_page_path,
        timeout=config.default_timeout
    )
