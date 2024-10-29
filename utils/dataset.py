import random
import string
from datetime import datetime
from datetime import timedelta

TEST_PAYEE_COMPANY_NAME = 'Test payee company name'


def generate_rtp_data():
    notice_number = ''.join([str(random.randint(0, 9)) for _ in range(18)])

    payer_fiscal_code = ''.join([str(random.randint(0, 9)) for _ in range(11)])

    amount = f"{random.randint(0, 999999)}"

    description = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 140)))

    expiry_date = (datetime.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')

    payee_company_name = TEST_PAYEE_COMPANY_NAME

    payee_fiscal_code = ''.join([str(random.randint(0, 9)) for _ in range(random.choice([11, 16]))])

    return {
        'noticeNumber': notice_number,
        'payerId': payer_fiscal_code,
        'amount': amount,
        'description': description,
        'expiryDate': expiry_date,
        'payeeCompanyName': payee_company_name,
        'payeeId': payee_fiscal_code
    }
