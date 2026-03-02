"""Utility to generate DS-05 ACTC compliant callback payloads for tests.

The generated payload mimics the callback sent for an asynchronous SEPA
Request-to-Pay response with both an `ACTC` (Accepted Technical Validation)
transaction status and an invalid one.
"""
import random
import uuid

from .datetime_utils import generate_create_time
from .datetime_utils import generate_execution_date
from .datetime_utils import generate_expiry_date
from .datetime_utils import generate_future_time
from .generators_utils import generate_random_digits
from .generators_utils import generate_random_string
from .iban_utils import generate_sepa_iban
from .text_utils import generate_transaction_id
from utils.text_utils import fake
from utils.type_utils import JsonType


ACTC_STATUS = 'ACTC'
INVALID_STATUS = 'INVALID'


def generate_callback_data_DS_05_ACTC_compliant(bic: str = 'MOCKSP04') -> JsonType:
    """Generate a DS-05 ACTC compliant callback payload.

    The payload simulates an asynchronous SEPA Request-to-Pay response
    with an accepted technical validation (`TxSts: ACTC`), including group
    header, original message information, payment details and HAL-style links.

    Args:
        bic: Bank Identifier Code of the initiating party
            (defaults to ``'MOCKSP04'``).

    Returns:
        JsonType: JSON-serializable DS-05 ACTC compliant callback payload,
        ready to be used in tests.
    """
    return _generate_callback_data_DS_05_ACTC(bic=bic, status=ACTC_STATUS)


def generate_invalid_callback_data_DS_05_ACTC(bic: str = 'MOCKSP04') -> JsonType:
    """Generate a DS-05 non-compliant callback payload with invalid status.

    The payload simulates an asynchronous SEPA Request-to-Pay response
    with an invalid transaction status, which can be used to test the
    system's handling of non-compliant callbacks.

    Args:
        bic: Bank Identifier Code of the initiating party
            (defaults to ``'MOCKSP04'``).

    Returns:
        JsonType: JSON-serializable DS-05 non-compliant callback payload with
        invalid status, ready to be used in tests.
    """
    return _generate_callback_data_DS_05_ACTC(bic=bic, status=INVALID_STATUS)


def _generate_callback_data_DS_05_ACTC(
    bic: str = 'MOCKSP04',
    status: str = ACTC_STATUS,
) -> JsonType:
    """Generate a DS-05  callback payload.

    The payload simulates an asynchronous SEPA Request-to-Pay response
    with an accepted technical validation (`TxSts: ACTC`), including group
    header, original message information, payment details and HAL-style links.

    Args:
        bic: Bank Identifier Code of the initiating party
            (defaults to ``'MOCKSP04'``).
        status: Transaction status to set in the payload (defaults to `ACTC`).

    Returns:
        JsonType: JSON-serializable DS-05 callback payload.
    """
    message_id = str(uuid.uuid4())
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"
    transaction_id = generate_transaction_id()

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    amount = round(random.uniform(1, 999999), 2)
    expiry_date = generate_expiry_date(1, 30)
    execution_date = generate_execution_date(1, 15)

    return {
        'resourceId': resource_id,
        'AsynchronousSepaRequestToPayResponse': {
            'resourceId': resource_id,
            'Document': {
                'CdtrPmtActvtnReqStsRpt': {
                    'GrpHdr': {
                        'MsgId': message_id,
                        'CreDtTm': create_time,
                        'InitgPty': {'Id': {'OrgId': {'AnyBIC': bic}}},
                    },
                    'OrgnlGrpInfAndSts': {
                        'OrgnlMsgId': original_msg_id,
                        'OrgnlMsgNmId': 'pain.013.001.07',
                        'OrgnlCreDtTm': original_time,
                    },
                    'OrgnlPmtInfAndSts': [
                        {
                            'OrgnlPmtInfId': str(uuid.uuid4()),
                            'TxInfAndSts': {
                                'StsId': message_id,
                                'OrgnlInstrId': f"TestRtpMessage{generate_random_string(20)}",
                                'OrgnlEndToEndId': generate_random_digits(18),
                                'TxSts': status,
                                'StsRsnInf': {
                                    'Orgtr': {'Id': {'OrgId': {'AnyBIC': bic}}},
                                },
                                'OrgnlTxRef': {
                                    'PmtTpInf': {
                                        'SvcLvl': {'Cd': 'SRTP'},
                                        'LclInstrm': {'Prtry': 'NOTPROVIDED'},
                                    },
                                    'RmtInf': {'Ustrd': fake.sentence()},
                                    'Cdtr': {
                                        'Id': {
                                            'OrgId': {
                                                'Othr': {
                                                    'Id': transaction_id,
                                                    'SchmeNm': {'Cd': 'BOID'},
                                                }
                                            }
                                        },
                                        'Nm': fake.company(),
                                    },
                                    'Dbtr': {
                                        'Id': {
                                            'PrvtId': {
                                                'Othr': {
                                                    'Id': transaction_id,
                                                    'SchmeNm': {'Cd': 'POID'},
                                                }
                                            }
                                        }
                                    },
                                    'DbtrAgt': {'FinInstnId': {'BICFI': bic}},
                                    'CdtrAgt': {'FinInstnId': {'BICFI': bic}},
                                    'CdtrAcct': {'Id': {'IBAN': generate_sepa_iban()}},
                                    'Amt': {'InstdAmt': amount},
                                    'ReqdExctnDt': {'Dt': f"{execution_date}Z"},
                                    'XpryDt': {'Dt': f"{expiry_date}Z"},
                                },
                            },
                        }
                    ],
                }
            },
        },
    }
