#send_to_gpd_queue.py
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator

import requests
from dotenv import load_dotenv

from utilities import random_iupd, random_iuv, require_env, to_epoch_millis
from config import GPD_TEST_BASE_URL

load_dotenv()


def str_to_bool(val: str) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


# CREATE: generate new records with fresh IDs
def generate_create_records(count: int) -> Iterable[Dict]:
    now = datetime.now(timezone.utc)
    operation = "CREATE"
    status = require_env("STATUS")
    debtor_cf = require_env("FISCAL_CODE")

    for i in range(count):
        ts = to_epoch_millis(now + timedelta(seconds=i))
        due = to_epoch_millis(now + timedelta(days=30, seconds=i))
        iuv = random_iuv(17)
        yield {
            "id": random_iuv(10),
            "operation": operation,
            "timestamp": ts,
            "iuv": iuv,
            "subject": "Performance Test RTP",
            "description": "Test RTP from queue API",
            "ec_tax_code": "80015010723",
            "debtor_tax_code": debtor_cf,
            "nav": f"3{iuv}",
            "due_date": due,
            "amount": 1500,
            "status": status,
            "psp_code": os.getenv("PSP_CODE") or None,
            "psp_tax_code": os.getenv("PSP_TAX_CODE") or None,
            "is_partial_payment": None,
        }


def read_source_lines(path: Path) -> Iterator[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# UPDATE: reuse IDs/iuv/nav from source and bump amount by +500
def generate_update_records(count: int, source_file: Path) -> Iterable[Dict]:
    now = datetime.now(timezone.utc)
    operation = "UPDATE"
    status = require_env("STATUS")
    debtor_cf = require_env("FISCAL_CODE")

    it = read_source_lines(source_file)
    for i in range(count):
        try:
            src = next(it)
        except StopIteration:
            break

        ts = to_epoch_millis(now + timedelta(seconds=i))
        due = to_epoch_millis(now + timedelta(days=30, seconds=i))
        new_amount = int(src.get("amount", 1500)) + 500

        yield {
            "id": src["id"],
            "operation": operation,
            "timestamp": ts,
            "iuv": src["iuv"],
            "subject": src.get("subject", "Performance Test RTP"),
            "description": src.get("description", "Test RTP from queue API"),
            "ec_tax_code": src.get("ec_tax_code", "80015010723"),
            "debtor_tax_code": debtor_cf,
            "nav": src["nav"],
            "due_date": due,
            "amount": new_amount,
            "status": status,
            "psp_code": os.getenv("PSP_CODE") or src.get("psp_code"),
            "psp_tax_code": os.getenv("PSP_TAX_CODE") or src.get("psp_tax_code"),
            "is_partial_payment": src.get("is_partial_payment"),
        }


# Write NDJSON to disk
def write_file(out_dir: Path, rows: int, op: str, source_file: Path | None) -> Path:
    filename = "createRTP.ndjson" if op == "CREATE" else "updateRTP.ndjson"
    out_path = out_dir / filename

    if op == "UPDATE":
        if not source_file or not source_file.exists():
            raise SystemExit("SOURCE_FILE required for UPDATE and must exist")
        records = generate_update_records(rows, source_file)
    else:
        records = generate_create_records(rows)

    written = 0
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            written += 1

    if written == 0:
        raise SystemExit("No records written")
    return out_path


# POST file to /send/gpd/file
def send_file_to_api(path: Path) -> Dict:
    api_url = f"{GPD_TEST_BASE_URL}/send/gpd/file"
    bulk = str_to_bool(require_env("BULK"))
    concurrency = int(require_env("CONCURRENCY"))
    params = {"bulk": "true" if bulk else "false", "concurrency": str(concurrency)}

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

    op_env = require_env("OPERATION").upper()
    if op_env not in {"CREATE", "UPDATE"}:
        raise SystemExit("OPERATION must be CREATE or UPDATE")

    source_file = out_dir / "createRTP.ndjson" if op_env == "UPDATE" else None

    out_path = write_file(out_dir, rows, op_env, source_file)
    print(f"[generator] {op_env} -> {out_path.resolve()}")

    result = send_file_to_api(out_path)
    print("[uploader] Response:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()