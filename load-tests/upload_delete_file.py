# upload_delete_file.py
import argparse
import json
from pathlib import Path

import requests
from utilities import require_env

from config import GPD_MASSIVE_BASE_URL

BASENAME_DELETE_PREFIX = 'testRTPDelete-'

def find_latest_zip(out_dir: Path, prefix: str = BASENAME_DELETE_PREFIX) -> Path:
    candidates = sorted(out_dir.glob(f"{prefix}*.zip"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No delete ZIP found in {out_dir} matching '{prefix}*.zip'")
    return candidates[0]

def upload_delete(zip_path: Path):
    broker = require_env('BROKER_CODE')
    org = require_env('ORG_FISCAL_CODE')
    ocp_key = require_env('GPD_API_KEY')

    url = f"{GPD_MASSIVE_BASE_URL}/brokers/{broker}/organizations/{org}/debtpositions/file"
    headers = {'ocp-apim-subscription-key': ocp_key}

    with zip_path.open('rb') as f:
        files = {'file': (zip_path.name, f, 'application/zip')}
        resp = requests.request('DELETE', url, headers=headers, files=files, timeout=60)

    print(json.dumps({
        'url': url,
        'zipPath': str(zip_path),
        'status': resp.status_code,
        'ok': 200 <= resp.status_code < 300,
        'responseText': resp.text[:1000],
    }, indent=2))

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Upload latest delete ZIP to GPD')
    p.add_argument('--zip-path', help='Explicit path (overrides auto-detect)')
    p.add_argument('--out-dir', help='Directory to search (default: OUT_DIR env)')
    p.add_argument('--prefix', default=BASENAME_DELETE_PREFIX, help='Filename prefix to match')
    return p.parse_args()

def main():
    args = parse_args()
    out_dir = Path(args.out_dir or require_env('OUT_DIR')).expanduser().resolve()
    zip_path = Path(args.zip_path).expanduser().resolve() if args.zip_path else find_latest_zip(out_dir, args.prefix)
    upload_delete(zip_path)

if __name__ == '__main__':
    main()
