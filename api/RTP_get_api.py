"""
API client module for retrieving RTP (Request To Pay) resources.

This module provides helper functions for interacting with RTP-related

Functions:
    - get_rtp: Fetch an RTP resource by its RTP ID.
    - get_rtp_by_notice_number: Fetch an RTP resource by its notice number.
    - get_rtp_delivery_status: Check the PD delivery status for a given notice number and payee ID.
"""

import uuid

import requests

from api.utils.api_version import GET_RTP_VERSION
from api.utils.endpoints import GET_RTP_BY_NOTICE_NUMBER_URL, GET_RTP_DELIVERY_STATUS_URL, GET_RTP_URL
from api.utils.http_utils import APPLICATION_JSON_HEADER, HTTP_TIMEOUT
from unittest.mock import Mock 


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
        "Version": GET_RTP_VERSION,
        "RequestId": str(uuid.uuid4()),
        **APPLICATION_JSON_HEADER,
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
        raise ValueError("access_token cannot be None")

    if not notice_number:
        raise ValueError("notice_number cannot be None")

    params = {"noticeNumber": notice_number}
    headers = {
        "Authorization": access_token,
        "Version": GET_RTP_VERSION,
        "RequestId": str(uuid.uuid4()),
        **APPLICATION_JSON_HEADER,
    }

    resp = requests.get(
        url=GET_RTP_BY_NOTICE_NUMBER_URL,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    return resp


def get_rtp_delivery_status(access_token: str, notice_number: str, payee_id: str):
    """
    Check the PD delivery status for a given notice number and payee ID.

    This endpoint always returns HTTP 200. The delivery outcome is encoded in the
    response body:
    - ``PD_RTP_DELIVERED``: an RTP with status SENT and no ERROR_SEND_RTP events
      was found for the given noticeNumber/payeeId pair.
    - ``PD_RTP_NOT_DELIVERED``: the notice number does not exist in the database,
      the payeeId does not match, or the RTP was not successfully delivered.

    Args:
        access_token (str): Bearer token with the ``payee_read_rtp`` role.
        notice_number (str): The NAV (notice number) identifying the debt position.
        payee_id (str): The creditor entity identifier (e.g. EC fiscal code).

    Returns:
        requests.Response: The HTTP response object returned by the API.
    """
    headers = {
        "Authorization": access_token,
        "Version": GET_RTP_VERSION,
        "RequestId": str(uuid.uuid4()),
        **APPLICATION_JSON_HEADER,
    }
    params = {
        "noticeNumber": notice_number,
        "payeeId": payee_id,
    }

    resp = requests.get(
        url=GET_RTP_DELIVERY_STATUS_URL,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    return resp

def get_rtp_optout_payees_list_mock():
    """
    Retrieve the list of payees that have opted out of receiving RTP messages.

    Returns:
        requests.Response: The HTTP response object returned by the API.
    """
    # Mock response for the list of payees that have opted out of receiving RTP messages
    # Mi mancano i dettagli dell'endpoint reale, quindi sto creando una risposta mock con dati di esempio
    # Ovviamente il test sarà adattato una volta che si conoscono i dettagli dell'endpoint reale e il formato della risposta
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "payeeId": "12345678901",
            "payeeName": "Regione Veneto",
            "optOut_Flag": True
        },
        {
            "payeeId": "98765432109",
            "payeeName": "Comune di Milano",
            "optOut_Flag": True
        },
        {
            "payeeId": "88760932207",
            "payeeName": "Regione Valle d'Aosta",
            "optOut_Flag": True
        }
    ]
    return mock_response

    
def get_institutions_service_consent_backoffice(service_id="RTP"):

    url = f"https://api.uat.platform.pagopa.it/backoffice/pagopa/services/v1/institutions/services/{service_id}/consents"

    headers = {
        "Ocp-Apim-Subscription-Key": "a3861f3a2b7540ffa9ede8c191f1be4c",
        "Accept": "application/json"
    }

    params = {
        "serviceId": "RTP",
        "pageNumber": 1,
        "pageSize": 10,
        "consent": "OPT_OUT",
        "toDate": "2026-04-09T23:59:59Z"
    }

    return requests.get(url=url, headers=headers, params=params)