import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from .constants_secrets_helper import DEBT_POSITIONS_ORGANIZATION_ID
from .fiscal_code_utils import fake_fc
from .generators_utils import generate_notice_number


def generate_debt_position_create_payload(debtor_fc=None, iupd=None, iuv=None):
    """
    Generate a payload for debt position creation.

    Args:
        debtor_fc (str, optional): Fiscal code of the debtor. If None, a new one is generated.
        iupd (str, optional): IUPD. If None, a new UUID is generated.
        iuv (str, optional): IUV. If None, a random 17-digit number is generated.

    Returns:
        dict: Debt position payload
    """
    if debtor_fc is None:
        debtor_fc = fake_fc()

    if iupd is None:
        iupd = uuid.uuid4().hex

    if iuv is None:
        iuv = generate_notice_number()

    now_utc = datetime.now(timezone.utc)
    due_date = (now_utc + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    retention_date = (now_utc + timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    org_fc = DEBT_POSITIONS_ORGANIZATION_ID
    payload = {
        'iupd': iupd,
        'type': 'F',
        'fiscalCode': debtor_fc,
        'fullName': 'ANTONELLO MUSTO',
        'streetName': 'streetName',
        'civicNumber': '11',
        'postalCode': '00100',
        'city': 'city',
        'province': 'RM',
        'region': 'RM',
        'country': 'IT',
        'email': 'lorem@lorem.com',
        'phone': '333-123456789',
        'companyName': 'companyName',
        'officeName': 'officeName',
        'switchToExpired': False,
        'paymentOption': [
            {
                'iuv': iuv,
                'amount': 10000,
                'description': 'Canone Unico Patrimoniale - CORPORATE',
                'isPartialPayment': False,
                'dueDate': due_date,
                'retentionDate': retention_date,
                'fee': 0,
                'transfer': [
                    {
                        'idTransfer': '1',
                        'amount': 10000,
                        'remittanceInformation': 'remittanceInformation 1',
                        'category': '9/0201133IM/',
                        'organizationFiscalCode': org_fc,
                        'iban': 'IT0000000000000000000000000'
                    }
                ]
            }
        ]
    }
    return payload
