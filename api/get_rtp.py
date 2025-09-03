"""
API client module for retrieving RTP (Request To Pay) resources.

This module provides helper functions for interacting with RTP-related
REST endpoints, using configuration values from `config.configuration.config`.

Functions:
    - get_rtp: Fetch an RTP resource by its RTP ID.
    - get_rtp_by_notice_number: Fetch an RTP resource by its notice number.
"""

import uuid
import requests
from config.configuration import config


GET_RTP_URL = config.rtp_creation_base_url_path + config.get_rtp_path
GET_RTP_BY_NOTICE_NUMBER_URL = config.rtp_creation_base_url_path + config.get_rtp_by_notice_number_path


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
        "Authorization": access_token,
        "Version": config.get_api_version,
        "RequestId": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    resp = requests.get(url=url, headers=headers, timeout=config.default_timeout)
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
        raise ValueError("access_token cannot be None")

    if not notice_number:
        raise ValueError("notice_number cannot be None")

    params = {"noticeNumber": notice_number}
    headers = {
        "Authorization": access_token,
        "Version": config.get_api_version,
        "RequestId": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    resp = requests.get(
        url=GET_RTP_BY_NOTICE_NUMBER_URL,
        params=params,
        headers=headers,
        timeout=config.default_timeout,
    )
    return resp
