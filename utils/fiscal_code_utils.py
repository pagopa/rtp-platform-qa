import random
from datetime import datetime
from datetime import timedelta

from faker import Faker

fake = Faker('it_IT')


def fake_fc(
    age: int = None,
    custom_month: int = None,
    custom_day: int = None,
    sex: str = None
) -> str:
    """Generate a fake fiscal code with customizable parameters.

    Args:
        age: Age of the fake fiscal code
        custom_month: Custom month for the fiscal code (1-12)
        custom_day: Custom day for the fiscal code (1-31)
        sex: Sex of the person ('M' or 'F')

    Returns:
        A fake fiscal code string
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

    return f"{surname}{name}{year}{month_letter}{day}X000{checksum}"


def month_number_to_fc_letter(month_num: int) -> str:
    """Convert month number to fiscal code letter.

    Args:
        month_num: Month number (1-12)

    Returns:
        Corresponding fiscal code letter
    """
    months = ['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T']
    if 1 <= int(month_num) <= 12:
        return months[int(month_num) - 1]
    else:
        return 'A'
