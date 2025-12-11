"""
API client module for retrieving RTP (Request To Pay) resources.

This module provides helper functions for interacting with RTP-related

Functions:
    - get_rtp: Fetch an RTP resource by its RTP ID.
    - get_rtp_by_notice_number: Fetch an RTP resource by its notice number.
"""
import uuid

import requests

from api.utils.api_version import GET_RTP_VERSION
from api.utils.endpoints import GET_RTP_BY_NOTICE_NUMBER_URL
from api.utils.endpoints import GET_RTP_URL
from api.utils.http_utils import APPLICATION_JSON_HEADER
from api.utils.http_utils import HTTP_TIMEOUT

def get_rtp(access_token: str, rtp_id: str):
    """
    Retrieve an RTP resource by its unique RTP identifier.

    Args:
        access_token (str): The bearer token used for authentication.
        rtp_id (str): The identifier of the RTP resource to fetch.

    Returns:
        requests.Response: The HTTP response object returned by the API.
    """
    url = GET_RTP_URL.format(rtpId=rtp_id)
    headers = {
        'Authorization': access_token,
        'Version': GET_RTP_VERSION,
        'RequestId': str(uuid.uuid4()),
        **APPLICATION_JSON_HEADER
    }

    resp = requests.get(url=url, headers=headers, timeout=HTTP_TIMEOUT)
    return resp


def get_rtp_by_notice_number(access_token: str, notice_number: str):
    """
    Retrieve an RTP resource by its notice number.

    Args:
        access_token (str): The bearer token used for authentication.
        notice_number (str): The notice number associated with the RTP resource.

    Returns:
        requests.Response: The HTTP response object returned by the API.
    """
    if not access_token:
        raise ValueError('access_token cannot be None')

    if not notice_number:
        raise ValueError('notice_number cannot be None')

    params = {'noticeNumber': notice_number}
    headers = {
        'Authorization': access_token,
        'Version': GET_RTP_VERSION,
        'RequestId': str(uuid.uuid4()),
        **APPLICATION_JSON_HEADER
    }

    resp = requests.get(
        url=GET_RTP_BY_NOTICE_NUMBER_URL,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    return resp
