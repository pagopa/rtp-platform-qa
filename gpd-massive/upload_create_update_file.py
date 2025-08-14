# upload_create_update_file.py
import json
from pathlib import Path
import requests
from activation import activate_random_cf
from generate_massive_zip import generate_massive_zip
from utilities import require_env
from config import GPD_MASSIVE_BASE_URL


# Activate a new fiscal code and generate the massive ZIP file
def activate_and_generate() -> Path:
    fiscal_code = activate_random_cf()
    print({"fiscal_code": fiscal_code})

    summary = generate_massive_zip(fiscal_code)
    print(json.dumps(summary, indent=2))
    return Path(summary["zipPath"])

# Upload the ZIP file using the GPD massive upload endpoint
def upload(zip_path: Path):
    broker = require_env("BROKER_CODE")
    org = require_env("ORG_FISCAL_CODE")
    ocp_key = require_env("GPD_API_KEY")
    url = f"{GPD_MASSIVE_BASE_URL}/brokers/{broker}/organizations/{org}/debtpositions/file"
    with zip_path.open("rb") as f:
        files = {"file": (zip_path.name, f, "application/zip")}
        headers = {"ocp-apim-subscription-key": ocp_key}
        resp = requests.post(url, headers=headers, files=files)
    print(json.dumps({
        "status": resp.status_code,
        "ok": resp.status_code == 202,
        "responseText": resp.text[:500]
    }, indent=2))

# Main execution
def main():
    zip_path = activate_and_generate()
    upload(zip_path)

if __name__ == "__main__":
    main()
