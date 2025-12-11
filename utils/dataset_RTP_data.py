import random

from .datetime_utils import generate_expiry_date
from .fiscal_code_utils import fake_fc
from .generators_utils import generate_notice_number
from .generators_utils import random_payee_id
from .text_utils import generate_random_description
from utils.constants_text_helper import TEST_PAYEE_COMPANY_NAME

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
