# cleanup_activation.py
import json
import uuid
from pathlib import Path

import requests
from auth import get_token
from utilities import require_env

from config import ACTIVATION_BASE_URL

ACTIVATION_PAYER_URL = f"{ACTIVATION_BASE_URL}/activations/payer"
ACTIVATION_DELETE_URL = f"{ACTIVATION_BASE_URL}/activations"

# Get activation ID by fiscal code
def get_activation_id(token: str) -> str:
    fiscal_code = require_env('FISCAL_CODE')
    headers = {
        'Version': 'v1',
        'RequestId': str(uuid.uuid4()),
        'payerId': f"{fiscal_code}",
        'Authorization': f"Bearer {token}",
    }
    resp = requests.get(ACTIVATION_PAYER_URL, headers=headers, data='', timeout=15)
    resp.raise_for_status()
    data = resp.json()
    activation_id = data.get('id')
    print(json.dumps({'activationId': activation_id}, indent=2))
    return activation_id

# Deactivate activation by ID
def deactivate_activation(token: str, activation_id: str):
    url = f"{ACTIVATION_DELETE_URL}/{activation_id}"
    headers = {
        'Version': 'v1',
        'RequestId': str(uuid.uuid4()),
        'Authorization': f"Bearer {token}"
    }
    resp = requests.delete(url, headers=headers, timeout=15)
    print(json.dumps({
        'status': resp.status_code,
        'ok': resp.status_code == 200,
        'responseText': resp.text[:500]
    }, indent=2))
    resp.raise_for_status()

# Remove local JSON/ZIP artifacts named testRTP-*.json|zip under OUT_DIR
def cleanup_local_artifacts() -> dict:
    out_dir = Path(require_env('OUT_DIR')).expanduser().resolve()
    deleted = []
    if out_dir.exists():
        for p in out_dir.iterdir():
            name = p.name
            if p.is_file() and (name.endswith('.json') or name.endswith('.zip') or name.endswith('.ndjson')):
                try:
                    p.unlink()
                    deleted.append(str(p))
                except Exception as e:
                    deleted.append(f"FAILED:{p} -> {e}")
    summary = {'outDir': str(out_dir), 'deletedCount': len(deleted), 'items': deleted}
    print(json.dumps({'cleanup': summary}, indent=2))
    return summary

def main():
    token = get_token()
    try:
        activation_id = get_activation_id(token)
        deactivate_activation(token, activation_id)
    finally:
        cleanup_local_artifacts()


if __name__ == '__main__':
    main()
