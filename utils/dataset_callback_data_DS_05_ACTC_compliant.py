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


def generate_callback_data_DS_05_ACTC_compliant(BIC: str = 'MOCKSP04') -> dict:
    """Generate DS-05 compliant callback data.

    Args:
        BIC: Bank Identifier Code

    Returns:
        Dictionary containing DS-05 compliant callback data
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
                        'InitgPty': {'Id': {'OrgId': {'AnyBIC': BIC}}},
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
                                'TxSts': 'ACTC',
                                'StsRsnInf': {
                                    'Orgtr': {'Id': {'OrgId': {'AnyBIC': BIC}}}
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
                                    'DbtrAgt': {'FinInstnId': {'BICFI': BIC}},
                                    'CdtrAgt': {'FinInstnId': {'BICFI': BIC}},
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
