"""Utility to generate invalid DS-12 RFC callback payloads for tests.

The generated payload mimics the callback that the callback-broker would
send for a SEPA Request-to-Pay Cancellation Response with an invalid status.
"""
from .dataset_callback_data_DS_12_base import generate_rfc_callback_data
from utils.type_utils import JsonType


INVALID_STATUS = 'INVALID'


def generate_callback_data_DS_12_invalid(
    bic: str = 'MOCKSP04',
    resource_id: str = None,
    original_msg_id: str = None,
    assignee_bic: str = None
) -> JsonType:
    """Generate a DS-12 invalid RFC callback payload.

    The payload simulates a SEPA Request-to-Pay Cancellation Response
    with an invalid status, indicating that the cancellation request is not valid.

    Args:
        bic: Bank Identifier Code of the debtor agent (default: 'MOCKSP04').
        resource_id: The resource ID of the RTP being cancelled (optional, generates random if not provided).
        original_msg_id: The original message ID without dashes (optional, generates random if not provided).
        assignee_bic: Bank Identifier Code of the assignee (default: 'MOCKSP04'). Used for certificate verification.

    Returns:
        JsonType: JSON-serializable DS-12 invalid callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``SepaRequestToPayCancellationResponse``: nested SEPA structure
              containing resolution of investigation with invalid status.
    """
    return generate_rfc_callback_data(
        status=INVALID_STATUS,
        bic=bic,
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic=assignee_bic
    )
