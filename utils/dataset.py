import random
import re
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from faker import Faker

from .datetime_utils import generate_create_time
from .datetime_utils import generate_execution_date
from .datetime_utils import generate_expiry_date
from .datetime_utils import generate_future_time
from .fiscal_code_utils import fake_fc
from .generators import generate_notice_number
from .generators import generate_random_digits
from .generators import generate_random_organization_id
from .generators import generate_random_string
from .generators import random_payee_id
from .iban_utils import generate_random_iban
from .iban_utils import generate_sepa_iban
from .text_utils import generate_random_description
from .text_utils import generate_transaction_id
from config.configuration import config
from config.configuration import secrets

fake = Faker('it_IT')

TEST_PAYEE_COMPANY_NAME = 'Test payee company name'

uuidv4_pattern = re.compile(
    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'
)


def generate_rtp_data(payer_id: str = '', payee_id: str = '', bic: str = '', amount: int = None) -> dict:
    """Generate RTP (Request to Pay) data for testing.

    Args:
        payer_id: Optional payer ID, generates random if not provided
        payee_id: Optional payee ID, generates random if not provided
        bic: Optional BIC code for debtor agent

    Returns:
        Dictionary containing payee, payer, and payment notice data
    """
    notice_number = generate_notice_number()
    if amount is None:
        amount = random.randint(0, 999999999)

    description = generate_random_description()
    expiry_date = generate_expiry_date()

    if not payer_id:
        payer_id = fake_fc()

    if not payee_id:
        payee_id = random_payee_id()

    payee = {
        'payeeId': payee_id,
        'name': TEST_PAYEE_COMPANY_NAME,
        'payTrxRef': 'ABC/124',
    }

    payer = {'name': 'Test Name', 'payerId': payer_id}

    payment_notice = {
        'noticeNumber': notice_number,
        'amount': amount,
        'description': description,
        'subject': 'Test payment notice',
        'expiryDate': expiry_date,
    }

    rtp_data = {'payee': payee, 'payer': payer, 'paymentNotice': payment_notice}

    if bic:
        rtp_data['bic'] = bic

    return rtp_data


def generate_epc_rtp_data(
    rtp_data: dict = None, payee_id: str = None, creditor_agent_id: str = None, bic: str = None
) -> dict:
    """Generate CBI-compliant RTP payload.

    Args:
        rtp_data: Optional RTP data to base the payload on
        payee_id: Optional payee ID to use (defaults to CBI_PAYEE_ID from secrets)
        creditor_agent_id: Optional creditor agent ID
        bic: Optional BIC code (deprecated, use rtp_data['bic'] instead)

    Returns:
        Dictionary containing CBI-compliant RTP payload
    """
    if not rtp_data:
        rtp_data = generate_rtp_data()

    if not payee_id:
        payee_id = secrets.cbi_payee_id

    if bic:
        rtp_data['bic'] = bic

    if not creditor_agent_id:
        creditor_agent_id = secrets.creditor_agent_id

    resource_id = str(uuid.uuid4())
    sanitized_id = resource_id.replace('-', '')

    initiating_party_id = generate_random_organization_id()
    organization_name = fake.company()
    creditor_iban = generate_random_iban()

    debtor_bic = bic

    return {
        'resourceId': resource_id,
        'Document': {
            'CdtrPmtActvtnReq': {
                'GrpHdr': {
                    'MsgId': sanitized_id,
                    'CreDtTm': datetime.now(timezone.utc)
                    .astimezone()
                    .isoformat(timespec='milliseconds'),
                    'NbOfTxs': '1',
                    'InitgPty': {
                        'Nm': organization_name,
                        'Id': {
                            'OrgId': {
                                'Othr': [
                                    {
                                        'Id': initiating_party_id,
                                        'SchmeNm': {'Cd': 'BOID'},
                                    }
                                ]
                            }
                        },
                    },
                },
                'PmtInf': [
                    {
                        'PmtInfId': rtp_data['paymentNotice']['noticeNumber'],
                        'PmtMtd': 'TRF',
                        'ReqdExctnDt': {'Dt': rtp_data['paymentNotice']['expiryDate']},
                        'XpryDt': {'Dt': rtp_data['paymentNotice']['expiryDate']},
                        'Dbtr': {
                            'Nm': rtp_data['payer']['name'],
                            'Id': {
                                'PrvtId': {
                                    'Othr': [
                                        {
                                            'Id': rtp_data['payer']['payerId'],
                                            'SchmeNm': {'Cd': 'POID'},
                                        }
                                    ]
                                }
                            },
                        },
                        'DbtrAgt': {'FinInstnId': {'BICFI': debtor_bic}},
                        'CdtTrfTx': [
                            {
                                'PmtId': {
                                    'InstrId': sanitized_id,
                                    'EndToEndId': rtp_data['paymentNotice'][
                                        'noticeNumber'
                                    ],
                                },
                                'PmtTpInf': {
                                    'SvcLvl': {'Cd': 'SRTP'},
                                    'LclInstrm': {'Prtry': 'PAGOPA'},
                                },
                                'Amt': {
                                    'InstdAmt': float(
                                        rtp_data['paymentNotice']['amount']
                                    )
                                },
                                'ChrgBr': 'SLEV',
                                'CdtrAgt': {
                                    'FinInstnId': {
                                        'Othr': {
                                            'Id': creditor_agent_id,
                                            'SchmeNm': {'Cd': 'BOID'},
                                        }
                                    }
                                },
                                'Cdtr': {
                                    'Nm': rtp_data['payee']['name'],
                                    'Id': {
                                        'OrgId': {
                                            'Othr': [
                                                {
                                                    'Id': payee_id,
                                                    'SchmeNm': {'Cd': 'BOID'},
                                                }
                                            ]
                                        }
                                    },
                                },
                                'CdtrAcct': {'Id': {'IBAN': creditor_iban}},
                                'InstrForCdtrAgt': [
                                    {
                                        'InstrInf': f"ATR113/{rtp_data['payee']['payTrxRef']}"
                                    },
                                    {'InstrInf': 'flgConf'},
                                ],
                                'RmtInf': {
                                    'Ustrd': [
                                        f"{rtp_data['paymentNotice']['subject']}/{rtp_data['paymentNotice']['noticeNumber']}",
                                        f"ATS001/{rtp_data['paymentNotice']['description']}",
                                    ]
                                },
                                'NclsdFile': [],
                            }
                        ],
                    }
                ],
            }
        },
        'callbackUrl': config.callback_url,
    }


def generate_callback_data_DS_04b_compliant(BIC: str = 'MOCKSP04') -> dict:
    """Generate DS-04b compliant callback data.

    Args:
        BIC: Bank Identifier Code

    Returns:
        Dictionary containing DS-04b compliant callback data
    """
    message_id = str(uuid.uuid4())
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    return {
        'resourceId': resource_id,
        'AsynchronousSepaRequestToPayResponse': {
            'CdtrPmtActvtnReqStsRpt': {
                'GrpHdr': {
                    'MsgId': message_id,
                    'CreDtTm': create_time,
                    'InitgPty': {'Id': {'OrgId': {'AnyBIC': BIC}}},
                },
                'OrgnlGrpInfAndSts': {
                    'OrgnlMsgId': original_msg_id,
                    'OrgnlMsgNmId': 'pain.013.001.08',
                    'OrgnlCreDtTm': original_time,
                },
                'OrgnlPmtInfAndSts': [{'TxInfAndSts': {'TxSts': ['RJCT']}}],
            }
        },
        '_links': {
            'initialSepaRequestToPayUri': {
                'href': f"https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/requests/{resource_id}",
                'templated': False,
            }
        },
    }


def generate_callback_data_DS_08N_compliant(BIC: str = 'MOCKSP04') -> dict:
    """Generate DS-08N compliant callback data.

    Args:
        BIC: Bank Identifier Code

    Returns:
        Dictionary containing DS-08N compliant callback data
    """
    message_id = str(uuid.uuid4())
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"
    transaction_id = generate_transaction_id()

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    # amount = random.randint(0, 999999999)
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
                                'TxSts': 'RJCT',
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

    # amount = random.randint(0, 999999999)
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


