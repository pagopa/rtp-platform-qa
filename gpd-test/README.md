# gpd-test

## Description

`gpd-test` is a microservice built with **FastAPI**, designed exclusively for testing the **GPD Event Hubs (Kafka-compatible)** queue. It allows you to simulate the creation, update, or deletion of an SRTP (SEPA Request to Pay) message directly on the queue, bypassing the GPD API. This enables isolated and controlled testing of downstream components.

---

## Main features

- REST Endpoints:
  - `POST /send/gpd/message`: sends a custom message to GPD
  - `POST /send/gpd/file`: uploads an NDJSON file and enqueues one message per line
  - `GET /health`: service health check
  - `GET /ready`: readiness check
- Secure retrieval of the **EventHub connection string** from **Azure Key Vault** using **Workload Identity**
- Docker image and Kubernetes deployment files
- Integrated GitHub Actions CI/CD workflow

---

## Technologies used

- Python 3.11  
- FastAPI  
- Kafka (EventHub-compatible)  
- Azure Key Vault + DefaultAzureCredential  
- Docker  
- GitHub Actions  
- Kubernetes (AKS)

---

## Run locally (quick start)

Requirements:

- Python 3.11+
- Azure CLI logged in (`az login`) if you use Key Vault locally

1. Create a virtualenv and install dev deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

1. Configure environment

The service fetches the Event Hubs connection string from Azure Key Vault via DefaultAzureCredential.
Set the following env vars (in your shell or a local `.env` at repo root):

- `KEYVAULT_NAME` = your Key Vault name
- `EVENTHUB_SECRET_NAME` = secret name containing the Event Hubs connection string
- `EVENTHUB_NAMESPACE` = Event Hubs namespace (used to build the Kafka bootstrap server host)
- `EVENTHUB_TOPIC` = Kafka topic to publish to

Notes:

- Locally, DefaultAzureCredential will use `az login` or environment credentials. In AKS it uses workload identity.
- If you experience auth issues locally, ensure `az account show` works for your tenant/subscription.

1. Start the API server

```bash
uvicorn gpd-test.main:app --reload --port 8080
```

The server logs will show ProducerService startup. If `EVENTHUB_NAMESPACE` or Key Vault envs are missing, startup will warn/fail and `/send/*` will return 5xx/503.

---

## Deployment on AKS

Deployment is handled via GitHub Actions:

- On push/merge to `main`, the service is automatically deployed to `itn-dev`
- Manually, you can trigger it from GitHub Actions > workflow `docker-publish.yml` by selecting `itn-dev` or `itn-uat`

Kubernetes manifests are located in `deploy/deploy-itn-dev.yaml` and `deploy/deploy-itn-uat.yaml`.

---

## Example requests

```bash
curl -X POST http://<your-domain>/send/gpd/message?validate=true \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "operation": "CREATE",
    "timestamp": 1722345600000,
    "iuv": "ABC123456789",
    "subject": "Pagamento TARI",
    "description": "TARI 2025 - Comune di Roma",
    "ec_tax_code": "12345678901",
    "debtor_tax_code": "ABCDEF12G34H567I",
    "nav": "NAV001",
    "due_date": 1725033600000,
    "amount": 1500,
    "status": "VALID",
    "psp_code": "PSP001",
    "psp_tax_code": "99988877766",
    "is_partial_payment": false
  }'
```

---

### Upload NDJSON (bulk)

```bash
curl -X POST "http://<your-domain>/send/gpd/file?rate=50&bulk=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/messages.ndjson"
```

Parameters:

- `rate` (int, default 10, 1..200): messages per second (token-bucket)
- `bulk` (bool, default false): if true, no in-flight cap (best effort at given rate)

Response (example):

```json
{
  "sent": 123,
  "failed": 2,
  "errors": [{"type": "ValidationError", "message": "..."}]
}
```

---

## Notes

- The `validate` boolean query parameter, if set to true, sends the message to the queue only if the payload complies with the [GdpMessage](https://github.com/pagopa/rtp-sender/blob/main/src/main/java/it/gov/pagopa/rtp/sender/domain/gdp/GdpMessage.java) format
- This API is internal only and works exclusively over VPN.

### Troubleshooting: timeouts

- Postman may have a short request timeout by default. Increase it in Settings → General → Request timeout (ms).
- If you are behind a proxy/APIM/Ingress, align its timeout (e.g., 120–240s) with the expected processing time.
- The server does not enforce a request timeout; it replies when the Kafka send completes. If producers are slow, the client/proxy may time out before the server answers.
