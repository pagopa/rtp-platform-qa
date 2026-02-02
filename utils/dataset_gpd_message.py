from datetime import datetime
from datetime import timedelta
from datetime import timezone

from utils.generators_utils import generate_random_digits

def generate_gpd_message_payload(fiscal_code: str, operation: str = 'CREATE', status: str = 'VALID'):
    """Generate a valid GPD message payload with dynamic values"""
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp() * 1000)
    due_date = int((now + timedelta(minutes=1)).timestamp() * 1000000)

    msg_id = int(generate_random_digits(16))
    iuv = generate_random_digits(17)

    payload = {
        'id': msg_id,
        'operation': operation,
        'timestamp': timestamp,
        'iuv': iuv,
        'subject': 'remittanceInformation 1',
        'description': 'Canone Unico Patrimoniale - CORPORATE - TEST',
        'ec_tax_code': '80015010723',
        'debtor_tax_code': fiscal_code,
        'nav': f"3{iuv}",
        'due_date': due_date,
        'amount': 30000,
        'status': status,
        'psp_code': None,
        'psp_tax_code': None
    }

    return payload
