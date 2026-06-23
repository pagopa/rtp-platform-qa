import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker("it_IT")

_FOREIGN_CODE_RANGES = [
    (100, 156),
    (200, 259),
    (300, 368),
    (400, 404),
    (500, 524),
    (600, 614),
    (700, 735),
    (800, 802),
    (900, 906),
]

_OMOCODIA_POSITIONS = [14, 13, 12, 10, 9, 7, 6]
_OMOCODIA_MAP = dict(zip("0123456789", "LMNPQRSTUV"))

_CF_ODD_VALUES = {
    "0": 1,
    "1": 0,
    "2": 5,
    "3": 7,
    "4": 9,
    "5": 13,
    "6": 15,
    "7": 17,
    "8": 19,
    "9": 21,
    "A": 1,
    "B": 0,
    "C": 5,
    "D": 7,
    "E": 9,
    "F": 13,
    "G": 15,
    "H": 17,
    "I": 19,
    "J": 21,
    "K": 2,
    "L": 4,
    "M": 18,
    "N": 20,
    "O": 11,
    "P": 3,
    "Q": 6,
    "R": 8,
    "S": 12,
    "T": 14,
    "U": 16,
    "V": 10,
    "W": 22,
    "X": 25,
    "Y": 24,
    "Z": 23,
}


def fake_fc(age: int = None, custom_month: int = None, custom_day: int = None, sex: str = None) -> str:
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
    municipality = fake_cf[11:15]
    checksum = fake_cf[15]

    if age is not None:
        year = (datetime.now() - timedelta(days=int(age) * 365)).strftime("%Y")[2:]

    if custom_month is not None and 1 <= custom_month <= 12:
        month_letter = month_number_to_fc_letter(custom_month)
    else:
        month_letter = fake_cf[8]

    if custom_day is not None and 1 <= custom_day <= 31:
        day = str(custom_day).zfill(2)
        if sex == "F":
            day = str(int(day) + 40)
        else:
            if int(day) > 31:
                day = str(int(day) - 40).zfill(2)
    else:
        day = fake_cf[9:11]

    return f"{surname}{name}{year}{month_letter}{day}{municipality}{checksum}"


def fake_omocodia_fc(level: int = None) -> str:
    """Generate a fake fiscal code with omocodia substitution.

    Args:
        level: Number of digit positions to substitute (1-7). Defaults to random.

    Returns:
        A fiscal code string with omocodia substitution applied.
    """
    if level is None:
        level = random.randint(1, 7)
    level = max(1, min(level, 7))

    cf = list(fake_fc())
    for pos in _OMOCODIA_POSITIONS[:level]:
        cf[pos] = _OMOCODIA_MAP[cf[pos]]
    cf[15] = _cf_checksum(cf)
    return "".join(cf)


def fake_fc_foreign(
    age: int = None,
    custom_month: int = None,
    custom_day: int = None,
    sex: str = None,
    country_code: str = None,
) -> str:
    """Generate a fake Italian fiscal code for a person born in a foreign country.

    The municipality code (positions 11–14) is replaced with a foreign country
    cadastral code (codice catastale estero), which always starts with 'Z'.

    Args:
        age: Age of the person.
        custom_month: Birth month (1–12).
        custom_day: Birth day (1–31).
        sex: Sex of the person ('M' or 'F').
        country_code: A specific foreign country cadastral code (e.g. 'Z110' for Germany).
                      If omitted, a random code is chosen from the valid ranges.

    Returns:
        A fake fiscal code string with a foreign country cadastral code.
    """
    if country_code is None:
        country_code = _random_foreign_code()

    base = fake_fc(age=age, custom_month=custom_month, custom_day=custom_day, sex=sex)
    return f"{base[:11]}{country_code}{base[15]}"


def fake_vat() -> str:
    """Generate a fake Italian VAT number (Partita IVA).

    A Partita IVA is an 11-digit string: 7 random digits, a 3-digit province
    code (001–100), and a Luhn-like check digit.

    Returns:
        An 11-digit string representing a valid Italian VAT number.
    """
    digits = [random.randint(0, 9) for _ in range(7)]
    province = random.randint(1, 100)
    digits += [province // 100, (province // 10) % 10, province % 10]
    digits.append(_vat_check_digit(digits))
    return "".join(map(str, digits))


def month_number_to_fc_letter(month_num: int) -> str:
    """Convert month number to fiscal code letter.

    Args:
        month_num: Month number (1-12)

    Returns:
        Corresponding fiscal code letter
    """
    months = ["A", "B", "C", "D", "E", "H", "L", "M", "P", "R", "S", "T"]
    if 1 <= int(month_num) <= 12:
        return months[int(month_num) - 1]
    else:
        return "A"


def _random_foreign_code() -> str:
    """Pick a random foreign country cadastral code from the valid ranges.

    Returns:
        A 4-character string starting with 'Z' followed by a 3-digit number
        within one of the valid ranges defined in _FOREIGN_CODE_RANGES.
    """
    lo, hi = random.choice(_FOREIGN_CODE_RANGES)
    return f"Z{random.randint(lo, hi)}"


def _vat_check_digit(digits: list) -> int:
    """Compute the check digit for an Italian VAT number (Partita IVA).

    Args:
        digits: The first 10 digits of the VAT number as a list of ints.

    Returns:
        The check digit (0–9).
    """
    odd_sum = sum(digits[i] for i in range(0, 10, 2))
    even_sum = sum(d * 2 if d * 2 < 10 else d * 2 - 9 for d in (digits[i] for i in range(1, 10, 2)))
    return (10 - (odd_sum + even_sum) % 10) % 10


def _cf_checksum(cf: list) -> str:
    """Compute the control character for an Italian fiscal code.

    Args:
        cf: The first 15 characters of the fiscal code as a list.

    Returns:
        The control character (A–Z).
    """
    total = sum(
        _CF_ODD_VALUES[c] if i % 2 == 0 else (ord(c) - ord("A") if c.isalpha() else int(c))
        for i, c in enumerate(cf[:15])
    )
    return chr(ord("A") + total % 26)
