from datetime import datetime
from datetime import timedelta
from datetime import timezone

from faker import Faker

from .fiscal_code_utils import fake_fc
from .generators import generate_random_digits
from .text_utils import generate_random_description

fake = Faker('it_IT')

def generate_producer_gpd_message_payload(
    operation='CREATE',
    ec_tax_code='80015010723',
    amount=30000,
    status='VALID',
    overrides=None
):
    """Generate a payload for sending a GPD message to the queue.

    Args:
        operation (str): Operation type (default: CREATE)
        ec_tax_code (str): EC tax code (default: 80015010723)
        amount (int): Amount in cents (default: 30000)
        status (str): Status (default: VALID)
        overrides (dict): Additional fields to override any value
    """
    if overrides is None:
        overrides = {}

    defaults = {
        'id': int(generate_random_digits(10)),
        'operation': operation,
        'ec_tax_code': ec_tax_code,
        'amount': amount,
        'status': status,
        'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
        'iuv': generate_random_digits(17),
        'subject': generate_random_description(),
        'description': 'Canone Unico Patrimoniale - CORPORATE - TEST',
        'debtor_tax_code': 'NPAPRL01D01X000Q',
        'nav': None,
        'due_date': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000),
        'psp_code': None, # max 50
        'psp_tax_code': None # max 50
    }

    payload = {**defaults, **overrides}

    if payload['nav'] is None:
        payload['nav'] = f"3{payload['iuv']}"

    return payload
