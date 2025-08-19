# activation.py
import uuid
from pathlib import Path

import requests
from dotenv import find_dotenv, set_key

from auth import get_token
from utilities import random_fiscal_code, require_env
from config import ACTIVATION_BASE_URL


ACTIVATION_URL = f"{ACTIVATION_BASE_URL}/activations"

def activate_random_cf() -> str:
    token = get_token()
    rtp_sp_id = require_env("SERVICE_PROVIDER")
    fiscal_code = random_fiscal_code()

    headers = {
        "Version": "v1",
        "RequestId": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    body = {"payer": {"fiscalCode": fiscal_code, "rtpSpId": rtp_sp_id}}

    resp = requests.post(ACTIVATION_URL, headers=headers, json=body, timeout=15)
    resp.raise_for_status()

    save_fiscal_code_to_env(fiscal_code)
    return fiscal_code

def save_fiscal_code_to_env(fiscal_code: str):
    env_path = find_dotenv(usecwd=True)
    if not env_path:
        # fallback: project root = two levels up from this file
        env_path = Path(__file__).resolve().parents[2] / ".env"
    set_key(str(env_path), "FISCAL_CODE", fiscal_code, quote_mode="never")

if __name__ == "__main__":
    cf = activate_random_cf()
    print(cf)
