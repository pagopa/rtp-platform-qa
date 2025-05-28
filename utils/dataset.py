import math
import random
import re
import string
import uuid
from datetime import datetime, timezone
from datetime import timedelta

from faker import Faker
from schwifty import IBAN

fake = Faker('it_IT')

TEST_PAYEE_COMPANY_NAME = 'Test payee company name'

uuidv4_pattern = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}')


def generate_rtp_data(payer_id: str = ''):
    notice_number = ''.join([str(random.randint(0, 9)) for _ in range(18)])

    amount = round(random.uniform(0, 999999999), 2)

    description = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=random.randint(0, 140)))

    expiry_date = (datetime.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')

    if not payer_id:
        payer_id = fake_fc()

    payee = {
        'payeeId': ''.join([str(random.randint(0, 9)) for _ in range(random.choice([11, 16]))]),
        'name': TEST_PAYEE_COMPANY_NAME,
        'payTrxRef': 'ABC/124'
    }

    payer = {
        'name': 'Test Name',
        'payerId': payer_id
    }

    payment_notice = {
        'noticeNumber': notice_number,
        'amount': amount,
        'description': description,
        'subject': 'Test payment notice',
        'expiryDate': expiry_date,
    }

    return {
        'payee': payee,
        'payer': payer,
        'paymentNotice': payment_notice
    }


def fake_fc(age: int = None, custom_month: int = None, custom_day: int = None, sex: str = None):
    """Faker wrapper that generates a fake fiscal code with customizable parameters.
    :param age: Age of the fake fiscal code.
    :param custom_month: Custom month for the fiscal code (1-12).
    :param custom_day: Custom day for the fiscal code (1-31).
    :param sex: Sex of the person ('M' or 'F').
    :returns: A fake fiscal code.
    :rtype: str
    """
    fake_cf = fake.ssn()

    surname = fake_cf[:3]
    name = fake_cf[3:6]
    year = fake_cf[6:8]
    checksum = fake_cf[15]

    if age is not None:
        year = (datetime.now() - timedelta(days=int(age) * 365)).strftime('%Y')[2:]

    if custom_month is not None and 1 <= custom_month <= 12:
        month_letter = month_number_to_fc_letter(custom_month)
    else:
        month_letter = fake_cf[8]

    if custom_day is not None and 1 <= custom_day <= 31:
        day = str(custom_day).zfill(2)
        if sex == 'F':
            day = int(day) + 40
        else:
            if int(day) > 31:
                day = str(int(day) - 40).zfill(2)
    else:
        day = fake_cf[9:11]

    return f'{surname}{name}{year}{month_letter}{day}X000{checksum}'


def month_number_to_fc_letter(month_num):
    months = ['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T']
    if 1 <= int(month_num) <= 12:
        return months[int(month_num) - 1]
    else:
        return 'A'


def generate_cbi_rtp_data(rtp_data: dict = None) -> dict:
    """Generates CBI-compliant RTP payload
    :param rtp_data: Optional RTP data to base the CBI payload on
    :returns: Dictionary containing CBI-compliant RTP payload
    """
    if not rtp_data:
        rtp_data = generate_rtp_data()

    resource_id = str(uuid.uuid4())
    sanitized_id = resource_id.replace('-', '')

    return {
        'resourceId': resource_id,
        'Document': {
            'CdtrPmtActvtnReq': {
                'GrpHdr': {
                    'MsgId': sanitized_id,
                    'CreDtTm': datetime.now(timezone.utc).astimezone().isoformat(timespec='milliseconds'),
                    'NbOfTxs': '1',
                    'InitgPty': {
                        'Nm': 'PagoPA',
                        'Id': {
                            'OrgId': {
                                'Othr': [{
                                    'Id': rtp_data['payee']['payeeId'],
                                    'SchmeNm': {'Cd': 'BOID'}
                                }]
                            }
                        }
                    }
                },
                'PmtInf': [{
                    'PmtInfId': rtp_data['paymentNotice']['noticeNumber'],
                    'PmtMtd': 'TRF',
                    'ReqdExctnDt': {
                        'Dt': rtp_data['paymentNotice']['expiryDate']
                    },
                    'XpryDt': {
                        'Dt': rtp_data['paymentNotice']['expiryDate']
                    },
                    'Dbtr': {
                        'Nm': rtp_data['payer']['name'],
                        'Id': {
                            'PrvtId': {
                                'Othr': [{
                                    'Id': rtp_data['payer']['payerId'],
                                    'SchmeNm': {
                                        'Cd': 'POID'
                                    }
                                }]
                            }
                        }
                    },
                    'DbtrAgt': {
                        'FinInstnId': {
                            'BICFI': 'UNCRITMM'
                        }
                    },
                    'CdtTrfTx': [{
                        'PmtId': {
                            'InstrId': sanitized_id,
                            'EndToEndId': rtp_data['paymentNotice']['noticeNumber']
                        },
                        'PmtTpInf': {
                            'SvcLvl': {
                                'Cd': 'SRTP'
                            },
                            'LclInstrm': {
                                'Prtry': 'PAGOPA'
                            }
                        },
                        'Amt': {
                            'InstdAmt': rtp_data['paymentNotice']['amount']
                        },
                        'ChrgBr': 'SLEV',
                        'CdtrAgt': {
                            'FinInstnId': {
                                'Othr': {
                                    'Id': rtp_data['payee']['payeeId'],
                                    'SchmeNm': {
                                        'Cd': 'BOID'
                                    }
                                }
                            }
                        },
                        'Cdtr': {
                            'Nm': rtp_data['payee']['name'],
                            'Id': {
                                'OrgId': {
                                    'Othr': [{
                                        'Id': rtp_data['payee']['payeeId'],
                                        'SchmeNm': {
                                            'Cd': 'BOID'
                                        }
                                    }]
                                }
                            }
                        },
                        'CdtrAcct': {
                            'Id': {
                                'IBAN': IBAN.generate('IT', bank_code='00000', account_code=str(
                                    round(random.random() * math.pow(10, 10))) + '99').compact
                            }
                        },
                        'InstrForCdtrAgt': [
                            {'InstrInf': rtp_data['payee']['payTrxRef']},
                            {'InstrInf': 'flgConf'}
                        ],
                        'RmtInf': {
                            'Ustrd': [
                                f"IMU/{rtp_data['paymentNotice']['noticeNumber']}",
                                'ATS001/IMU'
                            ]
                        },
                        'NclsdFile': []
                    }]
                }]
            }
        },
        'callbackUrl': "https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/send"
    }


def generate_callback_data_DS_04b_compliant(BIC: str = 'MOCKSP04') -> dict:
    message_id = str(uuid.uuid4())
    resource_id = f'TestRtpMessage{generate_random_string(16)}'
    original_msg_id = f'TestRtpMessage{generate_random_string(20)}'

    create_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    original_time = (datetime.now() + timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

    return {
        'resourceId': resource_id,
        'AsynchronousSepaRequestToPayResponse': {
            'CdtrPmtActvtnReqStsRpt': {
                'GrpHdr': {
                    'MsgId': message_id,
                    'CreDtTm': create_time,
                    'InitgPty': {
                        'Id': {
                            'OrgId': {
                                'AnyBIC': BIC
                            }
                        }
                    }
                },
                'OrgnlGrpInfAndSts': {
                    'OrgnlMsgId': original_msg_id,
                    'OrgnlMsgNmId': 'pain.013.001.08',
                    'OrgnlCreDtTm': original_time
                }
            }
        },
        '_links': {
            'initialSepaRequestToPayUri': {
                'href': f'https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/requests/{resource_id}',
                'templated': False
            }
        }
    }


def generate_callback_data_DS_08P_compliant(BIC: str = 'MOCKSP04') -> dict:
    message_id = str(uuid.uuid4())
    resource_id = f'TestRtpMessage{generate_random_string(16)}'
    original_msg_id = f'TestRtpMessage{generate_random_string(20)}'
    transaction_id = f'RTP-{generate_random_string(9)}-{int(datetime.now().timestamp() * 1000)}'

    create_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    original_time = (datetime.now() + timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

    amount = round(random.uniform(1, 999999), 2)
    expiry_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
    execution_date = (datetime.now() + timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d')

    return {
        'resourceId': resource_id,
        'AsynchronousSepaRequestToPayResponse': {
            'resourceId': resource_id,
            'Document': {
                'CdtrPmtActvtnReqStsRpt': {
                    'GrpHdr': {
                        'MsgId': message_id,
                        'CreDtTm': create_time,
                        'InitgPty': {
                            'Id': {
                                'OrgId': {
                                    'AnyBIC': BIC
                                }
                            }
                        }
                    },
                    'OrgnlGrpInfAndSts': {
                        'OrgnlMsgId': original_msg_id,
                        'OrgnlMsgNmId': 'pain.013.001.07',
                        'OrgnlCreDtTm': original_time
                    },
                    'OrgnlPmtInfAndSts': [
                        {
                            'OrgnlPmtInfId': str(uuid.uuid4()),
                            'TxInfAndSts': {
                                'StsId': message_id,
                                'OrgnlInstrId': f'TestRtpMessage{generate_random_string(20)}',
                                'OrgnlEndToEndId': ''.join(random.choices('0123456789', k=18)),
                                'TxSts': 'RJCT',
                                'StsRsnInf': {
                                    'Orgtr': {
                                        'Id': {
                                            'OrgId': {
                                                'AnyBIC': BIC
                                            }
                                        }
                                    }
                                },
                                'OrgnlTxRef': {
                                    'PmtTpInf': {
                                        'SvcLvl': {'Cd': 'SRTP'},
                                        'LclInstrm': {'Prtry': 'NOTPROVIDED'}
                                    },
                                    'RmtInf': {'Ustrd': fake.sentence()},
                                    'Cdtr': {
                                        'Id': {
                                            'OrgId': {
                                                'Othr': {
                                                    'Id': transaction_id,
                                                    'SchmeNm': {'Cd': 'BOID'}
                                                }
                                            }
                                        },
                                        'Nm': fake.company()
                                    },
                                    'Dbtr': {
                                        'Id': {
                                            'PrvtId': {
                                                'Othr': {
                                                    'Id': transaction_id,
                                                    'SchmeNm': {'Cd': 'POID'}
                                                }
                                            }
                                        }
                                    },
                                    'DbtrAgt': {
                                        'FinInstnId': {'BICFI': BIC}
                                    },
                                    'CdtrAgt': {
                                        'FinInstnId': {'BICFI': BIC}
                                    },
                                    'CdtrAcct': {
                                        'Id': {
                                            'IBAN': IBAN.generate('IT', bank_code='00000', account_code=str(
                                                round(random.random() * math.pow(10, 10))) + '99').compact
                                        }
                                    },
                                    'Amt': {'InstdAmt': amount},
                                    'ReqdExctnDt': {
                                        'Dt': f'{execution_date}Z'
                                    },
                                    'XpryDt': {
                                        'Dt': f'{expiry_date}Z'
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }


def generate_random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
