import requests

from api.utils.endpoints import LANDING_PAGE_URL
from api.utils.http_utils import HTTP_TIMEOUT

def landing_page():
    """API to get landing page
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.get(
        url=LANDING_PAGE_URL,
        timeout=HTTP_TIMEOUT
    )
