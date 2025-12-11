import uuid
from datetime import datetime
from datetime import timezone

from .constants_config_helper import CALLBACK_URL
from .constants_secrets_helper import CBI_PAYEE_ID
from .constants_secrets_helper import CREDITOR_AGENT_ID
from .dataset_RTP_data import generate_rtp_data
from .generators_utils import generate_random_organization_id
from .iban_utils import generate_random_iban
from utils.text_utils import fake


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
        payee_id = CBI_PAYEE_ID

    if bic:
        rtp_data['bic'] = bic

    if not creditor_agent_id:
        creditor_agent_id = CREDITOR_AGENT_ID

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
        'callbackUrl': CALLBACK_URL
    }
