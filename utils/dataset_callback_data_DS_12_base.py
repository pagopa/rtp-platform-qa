"""Base utility for generating RFC callback payloads for DS-12 callbacks.

This module provides a shared base function for generating SEPA Request-to-Pay
Cancellation Response callbacks with different status codes (CNCL, RJCR, etc.).
"""
import uuid

from .datetime_utils import generate_create_time
from .datetime_utils import generate_execution_date


def generate_rfc_callback_data(
    status: str,
    BIC: str = 'MOCKSP04',
    resource_id: str = None,
    original_msg_id: str = None,
    assignee_bic: str = None
) -> dict:
    """Generate an RFC callback payload with the specified status.

    This is a base function that generates SEPA Request-to-Pay Cancellation
    Response payloads. It's used by DS-12P and DS-12N callback generators.

    Args:
        status: Cancellation status code ('CNCL' for cancelled, 'RJCR' for rejected, etc.).
        BIC: Bank Identifier Code of the debtor agent (default: 'MOCKSP04').
        resource_id: The resource ID of the RTP being cancelled (optional, generates random if not provided).
        original_msg_id: The original message ID without dashes (optional, generates random if not provided).
        assignee_bic: Bank Identifier Code of the assignee (default: 'MOCKSP04'). Used for certificate verification.

    Returns:
        dict: JSON-serializable RFC callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``SepaRequestToPayCancellationResponse``: nested SEPA structure
              containing resolution of investigation with the specified status.
    """
    if assignee_bic is None:
        assignee_bic = 'MOCKSP04'
    message_id = original_msg_id if original_msg_id else str(uuid.uuid4()).replace('-', '')
    resource_id = resource_id if resource_id else str(uuid.uuid4())
    original_pmt_inf_id = resource_id
    cxl_sts_id = str(uuid.uuid4()).replace('-', '')
    original_end_to_end_id = f"302{'0' * 15}"

    create_time = generate_create_time()
    execution_date = generate_execution_date(1, 15)

    amount = 130.00
    creditor_id = '15376371009'

    return {
        'SepaRequestToPayCancellationResponse': {
            'Document': {
                'RsltnOfInvstgtn': {
                    'Assgnmt': {
                        'Assgne': {
                            'Agt': {
                                'FinInstnId': {
                                    'BICFI': assignee_bic
                                }
                            }
                        },
                        'Assgnr': {
                            'Pty': {
                                'Id': {
                                    'OrgId': {
                                        'Othr': [
                                            {
                                                'Id': creditor_id,
                                                'SchmeNm': {
                                                    'Cd': 'BOID'
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        'CreDtTm': create_time,
                        'Id': message_id
                    },
                    'CxlDtls': [
                        {
                            'OrgnlPmtInfAndSts': [
                                {
                                    'OrgnlPmtInfId': original_pmt_inf_id,
                                    'CxlStsId': cxl_sts_id,
                                    'CxlStsRsnInf': [
                                        {
                                            'AddtlInf': [
                                                f'ATS005/ {execution_date}'
                                            ],
                                            'Orgtr': {
                                                'Id': {
                                                    'OrgId': {
                                                        'AnyBIC': 'PPAYITR1XXX'
                                                    }
                                                }
                                            }
                                        }
                                    ],
                                    'OrgnlEndToEndId': original_end_to_end_id,
                                    'OrgnlTxRef': {
                                        'Amt': {
                                            'InstdAmt': amount
                                        },
                                        'Cdtr': {
                                            'Pty': {
                                                'Nm': 'PagoPA'
                                            }
                                        },
                                        'CdtrAcct': {
                                            'Id': {
                                                'IBAN': 'IT96K999999999900SRTPPAGOPA'
                                            }
                                        },
                                        'DbtrAgt': {
                                            'FinInstnId': {
                                                'BICFI': BIC
                                            }
                                        },
                                        'ReqdExctnDt': {
                                            'Dt': f'{execution_date}Z'
                                        }
                                    }
                                }
                            ]
                        }
                    ],
                    'Sts': {
                        'Conf': status
                    }
                }
            }
        },
        'resourceId': resource_id
    }
