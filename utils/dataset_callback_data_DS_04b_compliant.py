"""Utility to generate DS-04b compliant callback payloads for tests.

The generated payload mimics the callback that the callback-broker would
send for an asynchronous SEPA Request-to-Pay response with a rejected
transaction.
"""

import uuid

from utils.type_utils import JsonType

from .datetime_utils import generate_create_time, generate_future_time
from .generators_utils import generate_random_string

RJCT_STATUS = "RJCT"
INVALID_STATUS = "INVALID"


def generate_callback_data_DS_04b_compliant(bic: str = "MOCKSP04") -> JsonType:
    """Generate a DS-04b compliant callback payload.

    The payload simulates an asynchronous SEPA Request-to-Pay response
    with a rejected transaction status (`TxSts: RJCT`), including
    group header, original message information and HAL-style links.

    Args:
        bic: Bank Identifier Code of the initiating party (default: 'MOCKSP04').

    Returns:
        dict: JSON-serializable DS-04b compliant callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``AsynchronousSepaRequestToPayResponse``: nested SEPA structure
              containing group header, original message info and status.
            - ``_links.initialSepaRequestToPayUri.href``: URL of the initial request.
    """
    return _create_DS_04_data_with_status(bic, RJCT_STATUS)


def generate_non_compliant_callback_data_DS_04b(bic: str = "MOCKSP04") -> JsonType:
    """Generate a non compiant DS-04b callback payload.

    The payload simulates an asynchronous SEPA Request-to-Pay response
    with an invalid transaction status (`TxSts: INVALID`), including
    group header, original message information and HAL-style links.

    Args:
        bic: Bank Identifier Code of the initiating party (default: 'MOCKSP04').

    Returns:
        dict: JSON-serializable DS-04b compliant callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``AsynchronousSepaRequestToPayResponse``: nested SEPA structure
              containing group header, original message info and status.
            - ``_links.initialSepaRequestToPayUri.href``: URL of the initial request.
    """
    return _create_DS_04_data_with_status(bic, INVALID_STATUS)


def _create_DS_04_data_with_status(bic: str, status: str) -> JsonType:
    """
    Helper to create DS-04 compliant callback data with specified status.

    Args:
    - bic: Bank Identifier Code for the initiating party.
    - status: Transaction status to include in the callback (e.g., 'RJCT', 'ACCP').

    Returns:
    - JsonType: JSON-serializable dictionary representing the callback payload.
    """
    message_id = str(uuid.uuid4())
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    return {
        "resourceId": resource_id,
        "AsynchronousSepaRequestToPayResponse": {
            "CdtrPmtActvtnReqStsRpt": {
                "GrpHdr": {
                    "MsgId": message_id,
                    "CreDtTm": create_time,
                    "InitgPty": {"Id": {"OrgId": {"AnyBIC": bic}}},
                },
                "OrgnlGrpInfAndSts": {
                    "OrgnlMsgId": original_msg_id,
                    "OrgnlMsgNmId": "pain.013.001.08",
                    "OrgnlCreDtTm": original_time,
                },
                "OrgnlPmtInfAndSts": [{"TxInfAndSts": {"TxSts": [status]}}],
            }
        },
        "_links": {
            "initialSepaRequestToPayUri": {
                "href": f"https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/requests/{resource_id}",
                "templated": False,
            }
        },
    }
