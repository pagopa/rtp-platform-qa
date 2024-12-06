import random
import string
from datetime import datetime
from datetime import timedelta

from faker import Faker

fake = Faker('it_IT')

TEST_PAYEE_COMPANY_NAME = 'Test payee company name'


def generate_rtp_data(payer_id: str = '' ):
    notice_number = ''.join([str(random.randint(0, 9)) for _ in range(18)])

    amount = round(random.uniform(0, 99999999), 2)

    description = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 140)))

    expiry_date = (datetime.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')

    if not payer_id:
        payer_id = fake_fc()

    payee = {
        'payeeId': ''.join([str(random.randint(0, 9)) for _ in range(random.choice([11, 16]))]),
        'name': TEST_PAYEE_COMPANY_NAME
    }

    return {
        'noticeNumber': notice_number,
        'amount': amount,
        'description': description,
        'expiryDate': expiry_date,
        'payerId': payer_id,
        'payee': payee
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
        year = (datetime.datetime.now() - datetime.timedelta(days=int(age) * 365)).strftime('%Y')[2:]

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
