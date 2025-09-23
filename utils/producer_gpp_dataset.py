from datetime import datetime, timedelta, timezone
from faker import Faker

from .fiscal_code_utils import fake_fc
from .generators import generate_random_digits
from .text_utils import generate_random_description

fake = Faker('it_IT')

def generate_producer_gpd_message_payload(overrides: dict = None):
    """Generate a payload for sending a GPD message to the queue.
    
    :param overrides: Dictionary of fields to override defaults (e.g., {'timestamp': 1234567890}).
    :returns: Dictionary payload for the GPD message.
    """
    if overrides is None:
        overrides = {}
    
    defaults = {
        "id": int(generate_random_digits(10)),
        "operation": "CREATE",
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        "iuv": generate_random_digits(17),
        "subject": generate_random_description(),
        "description": generate_random_description(),
        "ec_tax_code": "80015010723",
        "debtor_tax_code": fake_fc(),
        "nav": None,
        "due_date": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000),
        "amount": 30000,
        "status": "VALID",
        "psp_code": None,
        "psp_tax_code": None
    }
    
    payload = {**defaults, **overrides}
    
    if payload["nav"] is None:
        payload["nav"] = f"3{payload['iuv']}"
    
    return payload