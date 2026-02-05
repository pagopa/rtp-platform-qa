"""Utility to generate DS-12N RJCR compliant RFC callback payloads for tests.

The generated payload mimics the callback that the callback-broker would
send for a SEPA Request-to-Pay Cancellation Response with a RJCR
(Rejected Cancellation Request) status.
"""
from .dataset_callback_data_DS_12_base import generate_rfc_callback_data


def generate_callback_data_DS_12N_RJCR_compliant(
    BIC: str = 'MOCKSP04',
    resource_id: str = None,
    original_msg_id: str = None,
    assignee_bic: str = None
) -> dict:
    """Generate a DS-12N RJCR compliant RFC callback payload.

    The payload simulates a SEPA Request-to-Pay Cancellation Response
    with a RJCR (Rejected Cancellation Request) status, indicating that the
    cancellation request has been rejected and the RTP remains active.

    Args:
        BIC: Bank Identifier Code of the debtor agent (default: 'MOCKSP04').
        resource_id: The resource ID of the RTP being cancelled (optional, generates random if not provided).
        original_msg_id: The original message ID without dashes (optional, generates random if not provided).
        assignee_bic: Bank Identifier Code of the assignee (default: 'MOCKSP04'). Used for certificate verification.

    Returns:
        dict: JSON-serializable DS-12N RJCR compliant callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``SepaRequestToPayCancellationResponse``: nested SEPA structure
              containing resolution of investigation with RJCR status.
    """
    return generate_rfc_callback_data(
        status='RJCR',
        BIC=BIC,
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic=assignee_bic
    )
