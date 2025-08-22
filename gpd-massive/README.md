# GPD Massive Test Utilities

## Overview
A set of Python scripts to automate the lifecycle of RTP activations and GPD massive uploads in UAT.

## Features
- Create an RTP activation (`activation.py`)
- Generate a massive debt position JSON + ZIP (`generate_massive_zip.py`)
- Upload the ZIP to the GPD massive endpoint to create an RTP (`upload_create_pd_file.py`)
- Upload a json (CREATE and UPDATE) directly to GPD queue (`send_to_gpd_queue.py`)
- Upload the ZIP to the GPD massive endpoint to delete an RTP (`upload_delete_file.py`)
- Deactivate an activation and delete local artifacts (`cleanup_activation.py`)

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
python gpd-massive/upload_create_pd_file.py
```

### 2. Create and send a json (CREATE and UPDATE)
```bash
python gpd-massive/send_to_gpd_queue.py
```

### 3. Delete an RTP
```bash
python gpd-massive/upload_delete_file.py
```

### 3. Cleanup activation and local artifacts
```bash
python gpd-massive/cleanup_activation.py
```



# Cosmos DB Cleanup Script
A Python script to find and delete specific records from an Azure Cosmos DB for MongoDB collection.

## Features

- Finds all records matching a specific filter (`serviceProviderDebtor`).
- Reports the total count of found records before doing anything.
- Asks for user confirmation in interactive mode to prevent accidental deletions.
- Uses a batching and sleep mechanism to avoid database throttling errors (HTTP 429).

---
## ⚙️ Setup

1.  **Create a Virtual Environment**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**
    Install the required Python libraries from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create Environment File**
    Create a file named `.env` in the root of the project and add your connection string. The script will automatically load this variable.
    ```env
    # .env
    COSMOS_DB_CONNECTION_STRING="mongodb+srv://..."
    SERVICE_PROVIDER=<RTP_SP_ID>
    ```

---
## ▶️ Usage
The script will show you how many records it will find, and you need to confirm (y) or decline (n) the execution.
It works deleting 20 records at time and waiting 1 seconds before to repeat the operation, to avoid problem with throttling.
You can modify this changing BATCH_SIZE (20) and SECONDS_TO_SLEEP (1).

Run the script without any arguments. It will prompt you for confirmation before deleting any data.

```bash
python cleanup_mongo.py
```

## Notes
- All environment variables are loaded automatically from `.env`
- Base URLs are configured in `config.py`
- Artifacts are saved in `gpd-massive/artifacts/`
- The activation script sets the fiscal code in the .env file so the cleanup script is automated
