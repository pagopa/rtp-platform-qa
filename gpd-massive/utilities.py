# utilities.py
import os
import uuid
import random
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

load_dotenv()

ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

def random_iupd(prefix: str = "testMassiveRTP", length: int = 5) -> str:
    rnd = "".join(random.choice(ALNUM) for _ in range(length))
    return f"{prefix}{rnd}"

def random_iuv(digits: int = 17) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(digits))

def get_current_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")

def calculate_dates(due_days: int = 30, retention_days: int = 60) -> tuple[str, str]:
    if due_days < 0 or retention_days <= due_days:
        raise ValueError("retention_days must be > due_days and non-negative")
    now = datetime.now(UTC)
    due_date = now + timedelta(days=due_days)
    retention_date = due_date + timedelta(days=(retention_days - due_days))
    return (
        due_date.isoformat().replace("+00:00", "Z"),
        retention_date.isoformat().replace("+00:00", "Z")
    )


def random_fiscal_code(length: int = 11) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))

def require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing environment variable: {name}")
    return val

def new_request_id() -> str:
    return str(uuid.uuid4())
