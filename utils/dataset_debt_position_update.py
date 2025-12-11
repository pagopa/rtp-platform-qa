from datetime import datetime
from datetime import timedelta
from datetime import timezone

from .fiscal_code_utils import fake_fc
from .generators_utils import generate_iuv


def generate_debt_position_update_payload(iupd, debtor_fc=None, iuv=None):
    """
    Generate a payload for debt position update.
    """
    if debtor_fc is None:
        debtor_fc = fake_fc()
    if iuv is None:
        iuv = generate_iuv()

    now = datetime.now(timezone.utc)
    due_date = now + timedelta(days=7)
    retention_date = now + timedelta(days=70)
    validity_date = now + timedelta(days=4)

    date_format = '%Y-%m-%dT%H:%M:%S.000'
    due_date_str = due_date.astimezone(timezone.utc).strftime(date_format)
    retention_date_str = retention_date.astimezone(timezone.utc).strftime(date_format)
    validity_date_str = validity_date.astimezone(timezone.utc).strftime(date_format)

    return {
        'iupd': iupd,
        'type': 'F',
        'fiscalCode': debtor_fc,
        'fullName': 'John Doe',
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
        'validityDate': validity_date_str,
        'paymentOption': [
            {
                'iuv': iuv,
                'amount': 9500,
                'description': 'Canone Unico Patrimoniale - CORPORATE Updated',
                'isPartialPayment': False,
                'dueDate': due_date_str,
                'retentionDate': retention_date_str,
                'fee': 0,
                'transfer': [
                    {
                        'idTransfer': '1',
                        'amount': 8000,
                        'remittanceInformation': 'remittanceInformation 1',
                        'category': '9/0301105TS/',
                        'iban': 'IT0000000000000000000000000'
                    },
                    {
                        'idTransfer': '2',
                        'amount': 1000,
                        'remittanceInformation': 'remittanceInformation 2',
                        'category': '9/0301105TS/',
                        'iban': 'IT0000000000000000000000000'
                    },
                    {
                        'idTransfer': '3',
                        'amount': 500,
                        'remittanceInformation': 'remittanceInformation 3',
                        'category': '9/0301105TS/',
                        'iban': 'IT0000000000000000000000000'
                    }
                ]
            }
        ]
    }
