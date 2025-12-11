import random
import string
import uuid

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length with letters and digits.

    Args:
        length: Length of the string to generate

    Returns:
        Random string containing letters and digits
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_organization_id() -> str:
    """Generate a random 11-digit organization ID.

    Returns:
        String containing 11 random digits
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])


def random_payee_id() -> str:
    """Generate a random payee ID, which can be either 11 or 16 digits long.

    Returns:
        String containing 11 or 16 random digits
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(random.choice([11, 16]))])


def generate_notice_number() -> str:
    """Generate a random 18-digit notice number.

    Returns:
        String containing 18 random digits
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(18)])


def generate_random_digits(length: int) -> str:
    """Generate a random string of digits.

    Args:
        length: Length of the digit string to generate

    Returns:
        String containing random digits
    """
    return ''.join(random.choices('0123456789', k=length))

def generate_iuv():
    """
    Generate a unique IUV (Identificativo Univoco Versamento).

    Returns:
        str: A random 17-digit number as string
    """
    return ''.join(random.choices('0123456789', k=17))

def generate_iupd():
    """
    Generate a unique IUPD (Identificativo Univoco Posizione Debitoria).

    Returns:
        str: A unique identifier using UUID4 in hexadecimal format
    """
    return uuid.uuid4().hex[:17]
