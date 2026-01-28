"""Utility to generate DS-12N RJCR compliant RFC callback payloads for tests.

The generated payload mimics the callback that the callback-broker would
send for a SEPA Request-to-Pay Cancellation Response with a RJCR
(Rejected Cancellation Request) status.
"""
import uuid

from .datetime_utils import generate_create_time
from .datetime_utils import generate_execution_date
from .datetime_utils import generate_future_time
from .generators_utils import generate_random_digits
from .iban_utils import generate_sepa_iban
from utils.text_utils import fake


def generate_callback_data_DS_12N_RJCR_compliant(BIC: str = 'MOCKSP04') -> dict:
    """Generate a DS-12N RJCR compliant RFC callback payload.

    The payload simulates a SEPA Request-to-Pay Cancellation Response
    with a RJCR (Rejected Cancellation Request) status, indicating that the
    cancellation request has been rejected and the RTP remains active.

    Args:
        BIC: Bank Identifier Code of the initiating party (default: 'MOCKSP04').

    Returns:
        dict: JSON-serializable DS-12N RJCR compliant callback payload with:
            - ``resourceId``: unique identifier of the RTP message.
            - ``SepaRequestToPayCancellationResponse``: nested SEPA structure
              containing resolution of investigation with RJCR status.
    """
    message_id = str(uuid.uuid4()).replace('-', '')
    resource_id = str(uuid.uuid4())
    original_msg_id = str(uuid.uuid4()).replace('-', '')
    cxl_sts_id = str(uuid.uuid4()).replace('-', '')
    original_end_to_end_id = f"302{generate_random_digits(15)}"
    original_instr_id = str(uuid.uuid4()).replace('-', '')

    create_time = generate_create_time()
    original_time = generate_future_time(1)
    execution_date = generate_execution_date(1, 15)

    amount = 130.00
    creditor_id = generate_random_digits(11)

    return {
        'SepaRequestToPayCancellationResponse': {
            'Document': {
                'RsltnOfInvstgtn': {
                    'Assgnmt': {
                        'Assgne': {
                            'Agt': {
                                'FinInstnId': {
                                    'BICFI': 'PPAYITR1XXX'
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
                            'TxInfAndSts': [
                                {
                                    'CxlStsId': cxl_sts_id,
                                    'CxlStsRsnInf': [
                                        {
                                            'AddtlInf': [
                                                'Cancellation request rejected by debtor service provider'
                                            ],
                                            'Orgtr': {
                                                'Id': {
                                                    'OrgId': {
                                                        'AnyBIC': BIC
                                                    }
                                                }
                                            }
                                        }
                                    ],
                                    'OrgnlEndToEndId': original_end_to_end_id,
                                    'OrgnlGrpInf': {
                                        'OrgnlCreDtTm': original_time,
                                        'OrgnlMsgId': original_msg_id,
                                        'OrgnlMsgNmId': 'pain.013.001.10'
                                    },
                                    'OrgnlInstrId': original_instr_id,
                                    'OrgnlTxRef': {
                                        'Amt': {
                                            'InstdAmt': amount
                                        },
                                        'Cdtr': {
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
                                                },
                                                'Nm': 'PagoPA'
                                            }
                                        },
                                        'CdtrAcct': {
                                            'Id': {
                                                'IBAN': generate_sepa_iban()
                                            }
                                        },
                                        'CdtrAgt': {
                                            'FinInstnId': {
                                                'Othr': {
                                                    'Id': creditor_id,
                                                    'SchmeNm': {
                                                        'Cd': 'BOID'
                                                    }
                                                }
                                            }
                                        },
                                        'DbtrAgt': {
                                            'FinInstnId': {
                                                'BICFI': BIC
                                            }
                                        },
                                        'PmtTpInf': {
                                            'LclInstrm': {
                                                'Prtry': 'PAGOPA'
                                            },
                                            'SvcLvl': [
                                                {
                                                    'Cd': 'SRTP'
                                                }
                                            ]
                                        },
                                        'ReqdExctnDt': {
                                            'Dt': f'{execution_date}Z'
                                        },
                                        'RmtInf': {
                                            'Ustrd': [
                                                fake.sentence()
                                            ]
                                        }
                                    },
                                    'RsltnRltdInf': {
                                        'Chrgs': [
                                            {
                                                'Agt': {
                                                    'FinInstnId': {
                                                        'BICFI': BIC
                                                    }
                                                },
                                                'Amt': {
                                                    'ActiveOrHistoricCurrencyAndAmount': amount,
                                                    'Ccy': 'EUR'
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ],
                    'Sts': {
                        'Conf': 'RJCR'
                    }
                }
            }
        },
        'resourceId': resource_id
    }
