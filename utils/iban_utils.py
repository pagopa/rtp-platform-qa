import math
import random
from schwifty import IBAN


def generate_random_iban() -> str:
    """Generate a random Italian IBAN for testing purposes.
    
    Returns:
        Compact IBAN string
    """
    return IBAN.generate(
        'IT',
        bank_code='00000',
        account_code=str(round(random.random() * pow(10, 12)))
    ).compact


def generate_sepa_iban() -> str:
    """Generate a random IBAN for SEPA transactions.
    
    Returns:
        Compact IBAN string with specific format for SEPA
    """
    account_code = str(round(random.random() * math.pow(10, 10))) + '99'
    return IBAN.generate(
        'IT',
        bank_code='00000',
        account_code=account_code
    ).compact
