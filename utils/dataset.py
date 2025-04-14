import math
import random
import re
import string
import uuid
from datetime import datetime
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

    return {
        'resourceId': resource_id,
        'Document': {
            'CdtrPmtActvtnReq': {
                'GrpHdr': {
                    'MsgId': resource_id,
                    'CreDtTm': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    'NbOfTxs': '1',
                    'InitgPty': {
                        'Nm': 'PagoPA'
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
                            'BICFI': 'FAKESP01'
                        }
                    },
                    'CdtTrfTx': [{
                        'PmtId': {
                            'InstrId': resource_id,
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
                        'InstrForCdtrAgt': [{
                            'InstrInf': rtp_data['payee']['payTrxRef']
                        }],
                        'RmtInf': {
                            'Ustrd': [rtp_data['paymentNotice']['description']]
                        },
                        'NclsdFile': []
                    }]
                }]
            }
        },
        'callbackUrl': 'http://spsrtp.api.uat.cstar.pagopa.it'
    }


def generate_callback_data(BIC: str = 'MOCKSP04') -> dict:
    return {
        'resourceId': '456789123-rtp-response-001',
        'AsynchronousSepaRequestToPayResponse': {
            'CdtrPmtActvtnReqStsRpt': {
                'GrpHdr': {
                    'MsgId': 'RESPONSE-MSG-001',
                    'CreDtTm': '2025-03-21T10:15:30',
                    'InitgPty': {
                        'Id': {
                            'OrgId': {
                                'AnyBIC': BIC
                            }
                        }
                    }
                },
                'OrgnlGrpInfAndSts': {
                    'OrgnlMsgId': 'ORIGINAL-REQ-001',
                    'OrgnlMsgNmId': 'pain.013.001.08',
                    'OrgnlCreDtTm': '2025-03-20T14:30:00'
                }
            }
        },
        '_links': {
            'initialSepaRequestToPayUri': {
                'href': 'https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/requests/123456789-original-req-001',
                'templated': False
            }
        }
    }
