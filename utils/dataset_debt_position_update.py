from datetime import datetime
from datetime import timedelta
from datetime import timezone

from .fiscal_code_utils import fake_fc
from .generators_utils import generate_iuv


def generate_debt_position_update_payload(iupd, debtor_fc=None, iuv=None, original_iuv=None):
    """
    Generate a payload for debt position update.
    
    Args:
        iupd: The IUPD from the original debt position (required)
        debtor_fc: Fiscal code (defaults to same as create if None)
        iuv: New IUV for the payment option (if None, uses original_iuv or generates new)
        original_iuv: The IUV from the original debt position (to maintain consistency)
    """
    if debtor_fc is None:
        debtor_fc = fake_fc()
    
    # Use original IUV if provided, otherwise use iuv param or generate new
    if original_iuv:
        iuv = original_iuv
    elif iuv is None:
        iuv = generate_iuv()

    now = datetime.now(timezone.utc)
    due_date = now + timedelta(days=7)
    retention_date = now + timedelta(days=70)

    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    due_date_str = due_date.astimezone(timezone.utc).strftime(date_format)
    retention_date_str = retention_date.astimezone(timezone.utc).strftime(date_format)

    return {
        'iupd': iupd,
        'type': 'F',
        'fiscalCode': debtor_fc,
        'fullName': 'LORENZO BIANCHI',
        'streetName': 'streetName',
        'civicNumber': '11',
        'postalCode': '00100',
        'city': 'city',
        'province': 'RM',
        'region': 'RM',
        'country': 'IT',
        'email': 'lorem@lorem.com',
        'phone': '333-123456829',
        'companyName': 'companyName',
        'officeName': 'officeName',
        'switchToExpired': False,
        'paymentOption': [
            {
                'iuv': iuv,
                'amount': 30000,
                'description': 'Canone Unico Patrimoniale - CORPORATE - TEST',
                'isPartialPayment': False,
                'dueDate': due_date_str,
                'retentionDate': retention_date_str,
                'fee': 0,
                'transfer': [
                    {
                        'idTransfer': '1',
                        'amount': 30000,
                        'organizationFiscalCode': '80015010723',
                        'remittanceInformation': 'remittanceInformation 1',
                        'category': '9/0201133IM/',
                        'iban': 'IT0000000000000000000000000'
                    }
                ]
            }
        ]
    }
