# Gpd-test

## Descrizione

`gpd-test` è un microservizio sviluppato con **FastAPI**, pensato esclusivamente per testare la coda **GPD EventHub**. Consente di simulare la creazione, modifica o cancellazione di un messaggio SRTP (SEPA Request to Pay) direttamente sulla coda, senza passare dalla GPD API. Questo permette test controllati e indipendenti per i componenti downstream.

---

## Funzionalità principali

- Endpoint REST:
  - `POST /send/gpd/message`: invia un messaggio custom a GPD
  - `GET /health`: verifica dello stato del servizio
- Recupero sicuro della **connessione EventHub** da **Azure Key Vault** tramite **Workload Identity**
- Immagine Docker e file di deploy Kubernetes
- Workflow CI/CD GitHub Actions integrato

---

## Tecnologie utilizzate

- Python 3.11
- FastAPI
- Kafka (EventHub compatibile)
- Azure Key Vault + DefaultAzureCredential
- Docker
- GitHub Actions
- Kubernetes (AKS)

---

## Deploy su AKS

Il deploy è gestito via GitHub Actions:

- Su push/merge su `main`, viene eseguito automaticamente su `itn-dev`
- Manualmente, si può lanciare da GitHub Actions > workflow `docker-publish.yml` scegliendo `itn-dev` o `itn-uat`

I file di manifest Kubernetes sono in `deploy/deploy-itn-dev.yaml` e `deploy/deploy-itn-uat.yaml`.

---

## Esempio di chiamata

```bash
curl -X POST http://localhost:8000/send/gpd/message?validate=true \
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

- Il parametro booleano `validate` se valorizzato a true, innietta il messaggio nella coda solo se il payload rispetta il payload [GdpMessage](https://github.com/pagopa/rtp-sender/blob/main/src/main/java/it/gov/pagopa/rtp/sender/domain/gdp/GdpMessage.java)
- L'API è interna e funziona solo con VPN
