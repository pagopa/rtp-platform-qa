# generate_zip.py
import json
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from utilities import random_iupd, random_iuv, get_current_timestamp, calculate_dates, require_env


BASENAME_PREFIX = "testRTP-"

# Build one payment position row
def build_row(fiscal_code: str, iupd: str, iuv: str) -> dict:
    due_iso, retention_iso = calculate_dates()
    return {
        "iupd": iupd,
        "type": "F",
        "payStandIn": False,
        "fiscalCode": fiscal_code,
        "fullName": "ANTONELLO MUSTO",
        "streetName": "streetName",
        "civicNumber": "11",
        "postalCode": "00100",
        "city": "city",
        "province": "RM",
        "region": "RM",
        "country": "IT",
        "email": "lorem@lorem.com",
        "phone": "333-123456829",
        "switchToExpired": False,
        "companyName": "companyName",
        "officeName": "officeName",
        "validityDate": None,
        "paymentOption": [{
            "iuv": iuv,
            "amount": 10000,
            "description": f"Test RTP Massive {get_current_timestamp()}",
            "isPartialPayment": False,
            "dueDate": due_iso,
            "retentionDate": retention_iso,
            "fee": 0,
            "transfer": [{
                "idTransfer": "1",
                "amount": 10000,
                "organizationFiscalCode": "80015010723",
                "remittanceInformation": "remittanceInformation 1",
                "category": "9/0201133IM/",
                "iban": "IT0000000000000000000000000",
            }],
        }],
    }

# Compute SHA256 checksum of a file
def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# Write JSON and ZIP files with same basename; returns (json_path, zip_path)
def write_files(payload: dict, out_dir: Path) -> tuple[Path, Path]:
    stamp = get_current_timestamp()
    basename = f"{BASENAME_PREFIX}{stamp}"
    json_name = f"{basename}.json"
    zip_name = f"{basename}.zip"

    json_path = out_dir / json_name
    zip_path = out_dir / zip_name

    json_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    json_path.write_bytes(json_bytes)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr(json_name, json_bytes)

    return json_path, zip_path

# Generate files using env defaults; returns a summary dict
def generate_massive_zip(fiscal_code: str) -> dict:
    rows = int(require_env("ROWS"))
    out_dir = require_env("OUT_DIR")
    out_path = Path(out_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    payment_positions = [
        build_row(fiscal_code, random_iupd(), random_iuv())
        for _ in range(rows)
    ]
    payload = {"paymentPositions": payment_positions}

    json_path, zip_path = write_files(payload, out_path)
    return {
        "jsonPath": str(json_path),
        "zipPath": str(zip_path),
        "rows": rows,
        "fiscalCode": fiscal_code,
        "zipSha256": compute_sha256(zip_path),
    }

# Parse command-line arguments
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RTP massive zip payload")
    parser.add_argument("fiscal_code", help="Fiscal code for all rows")
    return parser.parse_args()

# Main entrypoint for CLI usage
def main():
    args = parse_args()
    summary = generate_massive_zip(args.fiscal_code)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
