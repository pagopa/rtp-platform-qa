from datetime import datetime
from datetime import timedelta
from datetime import timezone

from utils.generators_utils import generate_random_digits

def generate_gpd_message_payload(fiscal_code: str, operation: str = 'CREATE', status: str = 'VALID', iuv_length: str = None, msg_id_length: int = None):
    """Generate a valid GPD message payload with dynamic values"""
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp() * 1000)
    due_date = int((now + timedelta(minutes=1)).timestamp() * 1000000)

    if msg_id_length is None:
        msg_id_length = int(generate_random_digits(16))
    if iuv_length is None:
        iuv_length = generate_random_digits(17)

    payload = {
        'id': msg_id_length,
        'operation': operation,
        'timestamp': timestamp,
        'iuv': iuv_length,
        'subject': 'remittanceInformation 1',
        'description': 'Canone Unico Patrimoniale - CORPORATE - TEST',
        'ec_tax_code': '80015010723',
        'debtor_tax_code': fiscal_code,
        'nav': f"3{iuv_length}",
        'due_date': due_date,
        'amount': 30000,
        'status': status,
        'psp_code': None,
        'psp_tax_code': None
    }

    return payload


def generate_gpd_delete_message_payload(msg_id: int):
    """Generate a GPD DELETE message payload with all data fields set to null."""
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp() * 1000)

    return {
        'id': msg_id,
        'operation': 'DELETE',
        'timestamp': timestamp,
        'iuv': None,
        'subject': None,
        'description': None,
        'ec_tax_code': None,
        'debtor_tax_code': None,
        'nav': None,
        'due_date': None,
        'amount': None,
        'status': None,
        'psp_code': None,
        'psp_tax_code': None
    }
