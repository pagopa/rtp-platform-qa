# Gpd-test

## Description

`gpd-test` is a microservice built with **FastAPI**, designed exclusively for testing the **GPD EventHub** queue. It allows you to simulate the creation, update, or deletion of an SRTP (SEPA Request to Pay) message directly on the queue, bypassing the GPD API. This enables isolated and controlled testing of downstream components.

---

## Main Features

- REST Endpoints:
  - `POST /send/gpd/message`: sends a custom message to GPD
  - `GET /health`: service health check
- Secure retrieval of the **EventHub connection string** from **Azure Key Vault** using **Workload Identity**
- Docker image and Kubernetes deployment files
- Integrated GitHub Actions CI/CD workflow

---

## Technologies Used

- Python 3.11  
- FastAPI  
- Kafka (EventHub-compatible)  
- Azure Key Vault + DefaultAzureCredential  
- Docker  
- GitHub Actions  
- Kubernetes (AKS)

---

## Deployment on AKS

Deployment is handled via GitHub Actions:

- On push/merge to `main`, the service is automatically deployed to `itn-dev`
- Manually, you can trigger it from GitHub Actions > workflow `docker-publish.yml` by selecting `itn-dev` or `itn-uat`

Kubernetes manifests are located in `deploy/deploy-itn-dev.yaml` and `deploy/deploy-itn-uat.yaml`.

---

## Example Request

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

## Note aggiuntive

- The `validate` boolean query parameter, if set to true, sends the message to the queue only if the payload complies with the [GdpMessage](https://github.com/pagopa/rtp-sender/blob/main/src/main/java/it/gov/pagopa/rtp/sender/domain/gdp/GdpMessage.java) format
- This API is internal only and works exclusively over VPN.
