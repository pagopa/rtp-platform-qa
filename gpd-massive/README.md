# GPD Massive Test Utilities

## Overview
A set of Python scripts to automate the lifecycle of RTP activations and GPD massive uploads in UAT.

## Features
- Create an RTP activation (`activation.py`)
- Generate a massive debt position JSON + ZIP (`generate_zip.py`)
- Upload the ZIP to the GPD massive endpoint (`upload-file.py`)
- Deactivate an activation and delete local artifacts (`activation-cleanup.py`)

## Requirements
- Python 3.11+
- `.env` file in the project root with:
  ```env
  SERVICE_PROVIDER=<RTP_SP_ID>
  BROKER_CODE=<BROKER_CODE>
  ORG_FISCAL_CODE=<ORG_FISCAL_CODE>
  GPD_API_KEY=<API_KEY>
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### 1. Create activation and upload ZIP
```bash
python gpd-massive/upload-file.py
```

### 2. Cleanup activation and local artifacts
```bash
python gpd-massive/cleanup.py
```

## Notes
- All environment variables are loaded automatically from `.env`
- Base URLs are configured in `config.py`
- Artifacts are saved in `gpd-massive/artifacts/`
- The activation script sets the fiscal code in the .env file so the cleanup script is automated
