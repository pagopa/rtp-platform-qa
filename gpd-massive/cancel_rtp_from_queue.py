#send_to_gpd_queue.py
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

import requests
from dotenv import load_dotenv

from utilities import require_env, to_epoch_millis
from config import GPD_TEST_BASE_URL

load_dotenv()


# CREATE: generate new records with fresh IDs
def generate_create_records(count: int, out_dir: Path) -> Iterable[Dict]:
    in_path = out_dir / "createRTP.ndjson"

    now = datetime.now(timezone.utc)
    operation = "DELETE"

    with in_path.open("r", encoding="utf-8", newline="\n") as file:
        for line in file:
            if line.strip():
                data = json.loads(line)
                ts = to_epoch_millis(now)
                yield {
                    "id": data["id"],
                    "operation": operation,
                    "timestamp": ts,
                    "iuv": None,
                    "subject": None,
                    "description": None,
                    "ec_tax_code": None,
                    "debtor_tax_code": None,
                    "nav": None,
                    "due_date": None,
                    "amount": 0,
                    "status": None,
                    "psp_code": None,
                    "psp_tax_code": None
                }



def write_file(out_dir: Path, rows: int) -> Path:
    out_path = out_dir / "deleteRTP.ndjson"

    records = generate_create_records(rows,out_dir)

    written = 0

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            written += 1

    if written == 0:
        raise SystemExit("No records written")
    return out_path


def str_to_bool(val: str) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y"}

def cancel_file_to_api(path: Path) -> Dict:
    api_url = f"{GPD_TEST_BASE_URL}/send/gpd/file"
    bulk = str_to_bool(require_env("BULK"))
    rate = int(require_env("RATE"))
    params = {"bulk": "true" if bulk else "false", "concurrency": str(rate)}

    with path.open("rb") as fh:
        files = {"file": (path.name, fh, "application/x-ndjson")}
        resp = requests.post(api_url, params=params, files=files, timeout=300)
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise SystemExit(f"HTTP {resp.status_code}: {resp.text.strip() or '<no body>'}")
    return resp.json()


def main() -> None:
    rows = int(require_env("ROWS"))
    out_dir = Path(require_env("OUT_DIR"))
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = write_file(out_dir, rows)

    result = cancel_file_to_api(out_path)
    print("[uploader] Response:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()