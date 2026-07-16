# RTP Platform Quality Assurance Repository

This repository contains a comprehensive test suite for the RTP (Request to Pay) platform, covering functional tests, BDD tests, UX tests, performance tests, and contract tests. Tests are implemented in Python (pytest / behave / playwright) and JavaScript (k6).

## Table of Contents

- [Setup](#setup)
- [Test Overview](#test-overview)
  - [Functional Tests](#functional-tests)
  - [BDD Tests](#bdd-tests)
  - [UX Tests](#ux-tests)
  - [Performance Tests](#performance-tests)
  - [Contract Tests](#contract-tests)
  - [Load Test Utilities](#load-test-utilities)
- [Secrets Management](#secrets-management-on-github)
- [Run Locally](#run-it-locally)
- [Project Structure](#project-structure)
- [Helper Scripts](#helper-scripts)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/pagopa/rtp-platform-qa.git
cd rtp-platform-qa
```

### 2. Get secrets

Copy `.env.example` to `.env` and fill in the real values:

```bash
cp .env.example .env
```

> **Configuration split:** secrets (client IDs, client secrets, certificates, fiscal codes) live in `.env`; non-secret settings (API base URLs, paths, timeouts) live in `config.yaml`.

### 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 4. Install dependencies for a specific test type

Dependencies are managed via `pyproject.toml` extras. Use the Makefile targets:

```bash
make install-functional    # pytest, allure-pytest, cryptography
make install-bdd           # behave, allure-behave
make install-ux            # pytest-playwright, playwright
make install-contract      # schemathesis, pytest
make install-dev           # pre-commit, pytest-asyncio
```

Or install everything at once:

```bash
./install-requirements.sh
```

For UX tests, also install browser binaries:

```bash
python -m playwright install
```

---

## Test Overview

### Functional Tests

Pytest-based tests covering all RTP platform API endpoints and service interactions.

- **Location:** `functional-tests/tests/`
- **Tool:** pytest + allure-pytest
- **Configuration:** `pyproject.toml` (`[tool.pytest.ini_options]`)
- **Run:**

```bash
make test-functional
# or
pytest functional-tests/tests/ -q
```

**Test modules:**

| Directory | Coverage |
|-----------|----------|
| `activation/` | Debtor activation create, get, list, deactivation, payer status (GET /activations/payer/{payerId}/status), security |
| `auth/` | OAuth2 / Keycloak token retrieval and bearer token format |
| `availability/` | Service availability checks |
| `callbacks/` | RTP callback scenarios DS-04, DS-05, DS-08, DS-12N, DS-12P |
| `cancel_rtp/` | RTP cancellation flows |
| `get_rtp/` | RTP retrieval and delivery status |
| `gpd_availability/` | GPD (Gestione Posizioni Debitorie) availability |
| `process_messages_sender/` | GPD message processing: CREATE, UPDATE, DELETE, UPDATE-before-CREATE |
| `send_rtp/` | RTP send flows for CBI, ICCREA, POSTE, mock providers |
| `service_registry/` | Service registry and payee registry queries |
| `takeover/` | Debtor takeover scenarios |

**pytest markers** (use `-m <marker>` to filter):

`activation`, `auth`, `keycloak`, `send`, `cbi`, `poste`, `iccrea`, `callback`, `cancel`, `deactivation`, `mock`, `debt_positions`, `get`, `webform`, `landing_page`, `happy_path`, `unhappy_path`, `real_integration`, `need_fix`

---

### BDD Tests

Behavior-Driven Development tests written in Gherkin, executed with Behave.

- **Location:** `bdd-tests/`
- **Tool:** behave + allure-behave
- **Feature files:** `bdd-tests/features/`
- **Step definitions:** `bdd-tests/steps/`
- **Shared setup:** `bdd-tests/environment.py`
- **Run:**

```bash
make test-bdd
# or
behave bdd-tests/features
```

**Feature files:**

| Domain | Features |
|--------|----------|
| `central_registry/` | `activation.feature`, `takeover.feature` |
| `creditor_service_provider/` | `cancel_RTP.feature`, `send_RTP_through_API.feature`, `send_RTP_through_web_page.feature` |

---

### UX Tests

Browser automation tests using Playwright to validate the RTP web interface.

- **Location:** `ux-tests/tests/`
- **Tool:** pytest-playwright
- **Run:**

```bash
make test-ux
# or
pytest ux-tests/tests/ -q
```

**Test files:**

- `test_RTP_submission.py` – RTP submission via web form
- `test_RTP_cancel.py` – RTP cancellation via web form

---

### Performance Tests

k6-based load tests for the RTP platform services.

- **Location:** `performance-tests/`
- **Tool:** [k6](https://k6.io/docs/get-started/installation/)
- **Run:**

```bash
cd performance-tests
./run-tests.sh <test-folder> <script.js> <output-format> [scenario]
```

**Parameters:**

| Parameter | Values |
|-----------|--------|
| `<test-folder>` | `tests/rtp-activator`, `tests/rtp-sender`, `tests/service-registry` |
| `<script.js>` | filename in the test folder (e.g. `activation-finder.js`) |
| `<output-format>` | `console`, `dashboard`, `json`, `prometheus` |
| `[scenario]` | `stress_test`, `soak_test`, `spike_test`, `stress_test_fixed_user`, `soak_test_fixed_user`, `spike_test_fixed_user` |

**Examples:**

```bash
# Console output, default stress test
./run-tests.sh tests/rtp-activator activation-finder.js console

# Interactive dashboard, spike test
./run-tests.sh tests/rtp-activator activation.js dashboard spike_test

# JSON output, soak test
./run-tests.sh tests/rtp-activator activation-finder.js json soak_test
```

**Test scripts:**

| Folder | Scripts |
|--------|---------|
| `tests/rtp-activator/` | `activation.js`, `activation-finder.js`, `deactivation-finder.js`, `get-activations-finder.js`, `get-by-fiscal-code-finder.js`, `takeover-finder.js` |
| `tests/rtp-sender/` | `callback-finder.js`, `gpd-message-finder.js`, `payees.js` |
| `tests/service-registry/` | `service-registry.js` |

**Shared utilities (`performance-tests/utils/`):**

| File | Purpose |
|------|---------|
| `utils.js` | Auth (`setupAuth`), random data generators, header builders, scenario options |
| `batch-utils.js` | Bulk data creation, array shuffling, group distribution |
| `metrics-utils.js` | Custom k6 metrics, time-window analysis, breaking-point detection |
| `reporting-utils.js` | Plain-text report generation, per-VU stats, teardown summaries |
| `summary-utils.js` | `createTestSummary`, `createHandleSummary` factory |
| `teardown-utils.js` | `createBatchProcessingTeardown`, `createActivationTeardown`, `createDeactivationTeardown` |
| `sender-payloads.js` | Payload builders for sender tests |

**Prerequisites:** k6 installed, `.env` file at project root with credentials (see [Secrets Management](#secrets-management-on-github)).

---

### Contract Tests

Schemathesis-based tests that validate service adherence to their OpenAPI specifications by generating random inputs.

- **Location:** `contract-tests/`
- **Tool:** schemathesis + pytest
- **Run:**

```bash
make test-contract
# or
pytest contract-tests/ -q
```

**Test files:**

- `test_activation.py` – Activation API contract
- `test_api_send_rtp.py` – RTP send API contract

---

### Load Test Utilities

Python utility scripts for GPD massive uploads, RTP lifecycle automation, and Cosmos DB maintenance. These are operational tools rather than automated test suites.

- **Location:** `load-tests/`
- **Tool:** Python 3.11+ (independent `requirements.txt`)
- **Full documentation:** `load-tests/README.md`

**Scripts:**

| Script | Purpose |
|--------|---------|
| `activation.py` | Create an RTP activation |
| `generate_massive_zip.py` | Generate a massive debt-position JSON + ZIP |
| `upload_create_pd_file.py` | Upload ZIP to GPD massive endpoint (CREATE) |
| `upload_delete_file.py` | Upload ZIP to GPD massive endpoint (DELETE) |
| `send_to_gpd_queue.py` | Send CREATE/UPDATE records directly to the GPD queue (single or continuous mode) |
| `cleanup_activation.py` | Deactivate an activation and remove local artifacts |
| `cleanup_mongo.py` | Batch-delete records from Azure Cosmos DB for MongoDB |
| `cancel_rtp_from_queue.py` | Cancel RTPs via queue message |
| `auth.py` | Authentication helpers |
| `utilities.py` | Shared utilities |

**Setup:**

```bash
cd load-tests
pip install -r requirements.txt
```

Requires a `.env` in the project root with `SERVICE_PROVIDER`, `BROKER_CODE`, `ORG_FISCAL_CODE`, `GPD_API_KEY` (for GPD scripts) and optionally `COSMOS_DB_CONNECTION_STRING` (for cleanup).

---

## Secrets Management on GitHub

GitHub Actions uses repository environment variables and secrets. All values must be set in the repository's [Environments settings](https://github.com/pagopa/rtp-platform-qa/settings/environments) for each environment (`dev`, `uat`, `prod` — currently `uat` is active).

Secrets must be updated manually by admins when rotated. The full list of required variables (with descriptions) is in [`.env.example`](.env.example).

**Variable groups:**

| Group | Variables |
|-------|-----------|
| Debtor Service Provider | `DEBTOR_SERVICE_PROVIDER_CLIENT_ID`, `_SECRET`, `_ID` |
| Debtor Service Provider B | `DEBTOR_SERVICE_PROVIDER_B_CLIENT_ID`, `_SECRET`, `_ID` |
| Debtor Service Provider C | `DEBTOR_SERVICE_PROVIDER_C_CLIENT_ID`, `_SECRET`, `_ID` |
| Creditor Service Provider | `CREDITOR_SERVICE_PROVIDER_CLIENT_ID`, `_SECRET`, `_ID` |
| RTP Consumer / Sender | `RTP_CONSUMER_CLIENT_ID`, `_SECRET` |
| RTP Reader | `RTP_READER_CLIENT_ID`, `_SECRET` |
| Read RTP Activations | `READ_RTP_ACTIVATIONS_CLIENT_ID`, `_SECRET` |
| PagoPA Integration | `PAGOPA_INTEGRATION_*_CLIENT_ID`, `*_CLIENT_SECRET` (3 clients) |
| CBI | `CBI_CLIENT_ID`, `_SECRET`, `_PFX_BASE64`, `_PFX_PASSWORD_BASE64`, `CBI_ACTIVATED_FISCAL_CODE`, `CBI_PAYEE_ID`, `CREDITOR_AGENT_ID` |
| Third-Party Providers | `POSTE_CLIENT_ID`, `_SECRET`, `POSTE_ACTIVATED_FISCAL_CODE`, `ICCREA_ACTIVATED_FISCAL_CODE` |
| Mock Service Provider | `DEBTOR_SERVICE_PROVIDER_MOCK_PFX_BASE64`, `_PASSWORD_BASE64`, `MOCK_*_FISCAL_CODE` (6 vars) |
| GPD (Debt Positions) | `DEBT_POSITIONS_SUBSCRIPTION_KEY`, `_ORGANIZATION_ID` (UAT + DEV), `EC_TAX_CODE` |
| Web Application | `WEBPAGE_USERNAME`, `WEBPAGE_PASSWORD`, `WEBPAGE_CLIENT_ID` |

<details>
<summary>Full variable reference (click to expand)</summary>

### Debtor Service Provider

| Variable | Description |
|----------|-------------|
| `DEBTOR_SERVICE_PROVIDER_CLIENT_ID` | Client ID for the primary debtor service provider |
| `DEBTOR_SERVICE_PROVIDER_ID` | Unique identifier for the primary debtor service provider |
| `DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET` | Client secret for the primary debtor service provider |

### Debtor Service Provider B

| Variable | Description |
|----------|-------------|
| `DEBTOR_SERVICE_PROVIDER_B_CLIENT_ID` | Client ID for the secondary debtor service provider |
| `DEBTOR_SERVICE_PROVIDER_B_ID` | Unique identifier for the secondary debtor service provider |
| `DEBTOR_SERVICE_PROVIDER_B_CLIENT_SECRET` | Client secret for the secondary debtor service provider |

### Debtor Service Provider C

| Variable | Description |
|----------|-------------|
| `DEBTOR_SERVICE_PROVIDER_C_CLIENT_ID` | Client ID for debtor service provider MOCKSP05, used in send/cancel v2 EPC mock tests |
| `DEBTOR_SERVICE_PROVIDER_C_ID` | Unique identifier for debtor service provider MOCKSP05 |
| `DEBTOR_SERVICE_PROVIDER_C_CLIENT_SECRET` | Client secret for debtor service provider MOCKSP05 |

### Creditor Service Provider

| Variable | Description |
|----------|-------------|
| `CREDITOR_SERVICE_PROVIDER_CLIENT_ID` | Client ID for the creditor service provider |
| `CREDITOR_SERVICE_PROVIDER_ID` | Unique identifier for the creditor service provider |
| `CREDITOR_SERVICE_PROVIDER_CLIENT_SECRET` | Client secret for the creditor service provider |

### PagoPA Integration

| Variable | Description |
|----------|-------------|
| `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_ID` | Client ID for the PagoPA payee registry |
| `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_SECRET` | Client secret for the PagoPA payee registry |
| `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CONSENT_CLIENT_ID` | Client ID for the PagoPA payee registry consent |
| `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CONSENT_CLIENT_SECRET` | Client secret for the PagoPA payee registry consent |
| `PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_ID` | Client ID for the PagoPA service registry |
| `PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_SECRET` | Client secret for the PagoPA service registry |

### RTP Reader

| Variable | Description |
|----------|-------------|
| `RTP_READER_CLIENT_ID` | Client ID for the RTP Reader service |
| `RTP_READER_CLIENT_SECRET` | Client secret for the RTP Reader service |

### Web Application

| Variable | Description |
|----------|-------------|
| `WEBPAGE_USERNAME` | Username for web application login |
| `WEBPAGE_PASSWORD` | Password for web application login |
| `WEBPAGE_CLIENT_ID` | Client ID for web application authentication |

### CBI Configuration

| Variable | Description |
|----------|-------------|
| `CBI_CLIENT_ID` | Client ID for CBI service |
| `CBI_CLIENT_SECRET` | Client secret for CBI service |
| `CBI_CLIENT_PFX_BASE64` | Base64-encoded PFX certificate for CBI client |
| `CBI_CLIENT_PFX_PASSWORD_BASE64` | Base64-encoded password for the CBI PFX certificate |
| `CBI_ACTIVATED_FISCAL_CODE` | Fiscal code pre-activated for CBI tests |
| `CBI_PAYEE_ID` | CBI payee ID |
| `CREDITOR_AGENT_ID` | Creditor agent ID |

### Mock Service Provider

| Variable | Description |
|----------|-------------|
| `DEBTOR_SERVICE_PROVIDER_MOCK_PFX_BASE64` | Base64-encoded PFX certificate for mock debtor service provider |
| `DEBTOR_SERVICE_PROVIDER_MOCK_PFX_PASSWORD_BASE64` | Base64-encoded PFX password for mock debtor service provider |
| `MOCK_ACTC_FISCAL_CODE` | Fiscal code that triggers a synchronous ACTC response (DS-05) |
| `MOCK_RJCT_FISCAL_CODE` | Fiscal code that triggers a synchronous RJCT response (DS-08P N) |
| `MOCK_NO_LINKS_FISCAL_CODE` | Fiscal code that triggers a synchronous ACTC response without the `_links` field |
| `MOCK_EXTRA_FIELD_FISCAL_CODE` | Fiscal code that triggers a synchronous non-compliant ACTC-like response with an unexpected extra field; the RTP status remains `SENT` |
| `MOCK_RJCT_EXTRA_FIELD_FISCAL_CODE` | Fiscal code that triggers a synchronous RJCT non-compliant with an unexpected extra field |
| `MOCK_RJCT_NO_LINKS_FISCAL_CODE` | Fiscal code that triggers a synchronous RJCT without the `_links` field |

### Third-Party Providers

| Variable | Description |
|----------|-------------|
| `POSTE_CLIENT_ID` | Client ID for Poste Italiane service |
| `POSTE_CLIENT_SECRET` | Client secret for Poste Italiane service |
| `POSTE_ACTIVATED_FISCAL_CODE` | Fiscal code pre-activated for Poste Italiane tests |
| `ICCREA_ACTIVATED_FISCAL_CODE` | Fiscal code pre-activated for ICCREA tests |

### Read RTP Activations

| Variable | Description |
|----------|-------------|
| `READ_RTP_ACTIVATIONS_CLIENT_ID` | Client ID for the read-activations service client |
| `READ_RTP_ACTIVATIONS_CLIENT_SECRET` | Client secret for the read-activations service client |

### GPD (Debt Positions)

| Variable | Description |
|----------|-------------|
| `DEBT_POSITIONS_SUBSCRIPTION_KEY` | GPD subscription key (UAT) |
| `DEBT_POSITIONS_ORGANIZATION_ID` | GPD organization ID (UAT) |
| `DEBT_POSITIONS_DEV_SUBSCRIPTION_KEY` | GPD subscription key (DEV) |
| `DEBT_POSITIONS_DEV_ORGANIZATION_ID` | GPD organization ID (DEV) |
| `EC_TAX_CODE` | EC fiscal code used in GPD message payloads and debt position updates |

### RTP Consumer / Sender

| Variable | Description |
|----------|-------------|
| `RTP_CONSUMER_CLIENT_ID` | Client ID used by the consumer to authenticate to the sender |
| `RTP_CONSUMER_CLIENT_SECRET` | Client secret used by the consumer to authenticate to the sender |

</details>

---

## Run It Locally

Copy `.env.example` to `.env`, fill in the real values, then follow the [Setup](#setup) steps.

---

## Project Structure

```text
rtp-platform-qa/
├── api/                                      # Shared API client modules
│   ├── auth_api.py
│   ├── debtor_activation_api.py
│   ├── debtor_deactivation_api.py
│   ├── debtor_service_provider_api.py
│   ├── debtor_takeover_api.py
│   ├── GPD_debt_position_api.py
│   ├── RTP_callback_api.py
│   ├── RTP_cancel_api.py
│   ├── RTP_get_api.py
│   ├── RTP_landing_page_api.py
│   ├── RTP_process_sender.py
│   ├── RTP_send_api.py
│   ├── service_registry_payee_registry_api.py
│   ├── servise_registry_service_providers_api.py
│   └── utils/
│       ├── api_version.py
│       ├── endpoints.py
│       └── http_utils.py
├── bdd-tests/
│   ├── features/
│   │   ├── central_registry/
│   │   │   ├── activation.feature
│   │   │   └── takeover.feature
│   │   └── creditor_service_provider/
│   │       ├── cancel_RTP.feature
│   │       ├── send_RTP_through_API.feature
│   │       └── send_RTP_through_web_page.feature
│   ├── steps/
│   │   ├── activation_steps.py
│   │   ├── auth_steps.py
│   │   ├── cancel_rtp_steps.py
│   │   ├── dataset_steps.py
│   │   ├── debtor_steps.py
│   │   ├── send_rtp_steps.py
│   │   └── takeover_steps.py
│   └── environment.py
├── config/
│   └── configuration.py
├── contract-tests/
│   ├── test_activation.py
│   └── test_api_send_rtp.py
├── functional-tests/
│   └── tests/
│       ├── activation/
│       ├── auth/
│       ├── availability/
│       ├── callbacks/
│       ├── cancel_rtp/
│       ├── get_rtp/
│       ├── gpd_availability/
│       ├── process_messages_sender/
│       ├── send_rtp/
│       ├── service_registry/
│       ├── takeover/
│       └── conftest.py
├── load-tests/                                   # GPD massive & Cosmos DB operational utilities
│   ├── activation.py
│   ├── auth.py
│   ├── cancel_rtp_from_queue.py
│   ├── cleanup_activation.py
│   ├── cleanup_mongo.py
│   ├── config.py
│   ├── generate_massive_zip.py
│   ├── send_to_gpd_queue.py
│   ├── upload_create_pd_file.py
│   ├── upload_delete_file.py
│   ├── utilities.py
│   ├── requirements.txt
│   └── README.md
├── performance-tests/
│   ├── config/
│   │   └── config.js
│   ├── script/                               # One-off data setup scripts
│   │   ├── create-activation-otp.js
│   │   ├── create-activations.js
│   │   ├── create-gpd-message.js
│   │   ├── create-rtp.js
│   │   └── create-rtp-cancel.js
│   ├── tests/
│   │   ├── rtp-activator/
│   │   ├── rtp-sender/
│   │   └── service-registry/
│   ├── utils/
│   │   ├── batch-utils.js
│   │   ├── metrics-utils.js
│   │   ├── reporting-utils.js
│   │   ├── sender-payloads.js
│   │   ├── summary-utils.js
│   │   ├── teardown-utils.js
│   │   └── utils.js
│   ├── run-tests.sh
│   └── README.md
├── utils/                                    # Shared Python utilities
│   ├── activation_helpers.py
│   ├── callback_builder.py
│   ├── constants_config_helper.py
│   ├── constants_secrets_helper.py
│   ├── constants_text_helper.py
│   ├── cryptography_utils.py
│   ├── dataset_callback_data_DS_*.py         # Callback payload builders (DS-04b, DS-05, DS-08N, DS-08P, DS-12)
│   ├── dataset_debt_position_create.py
│   ├── dataset_debt_position_update.py
│   ├── dataset_EPC_RTP_data.py
│   ├── dataset_gpd_message.py
│   ├── dataset_RTP_data.py
│   ├── datetime_utils.py
│   ├── extract_next_activation_id.py
│   ├── fiscal_code_utils.py
│   ├── generator_random_values_utils.py
│   ├── generators_utils.py
│   ├── http_utils.py
│   ├── iban_utils.py
│   ├── idempotency_key_utils.py
│   ├── log_sanitizer_helper.py
│   ├── regex_utils.py
│   ├── response_assertions_utils.py
│   ├── rtp_send_helpers.py
│   ├── test_expectations.py
│   ├── text_utils.py
│   └── type_utils.py
├── ux-tests/
│   └── tests/
│       ├── conftest.py
│       ├── test_RTP_cancel.py
│       └── test_RTP_submission.py
├── .github/
│   └── workflows/
│       ├── run_tests.yml                     # Main CI: functional + BDD tests with Allure
│       ├── doc_page.yaml                     # GitHub Pages deployment (MkDocs + Allure reports)
│       ├── send_slack_notification.yml       # Slack notifications
│       ├── manual_debt_position_tests.yml    # Manual trigger for GPD tests
│       └── extract_allure_fail_rate.yml      # Allure failure rate extraction
├── generate-allure-report.sh
├── install-requirements.sh
├── sanitize-allure-results.py                # Strips secrets from Allure results before publication
├── .env.example                              # Template for local .env (copy and fill in)
├── Makefile
└── pyproject.toml
```

---

## Helper Scripts

### `install-requirements.sh`

Installs all Python dependencies for all test suites.

```bash
./install-requirements.sh
```

Equivalent to running all `make install-*` targets.

### `generate-allure-report.sh`

Runs all main test suites and generates a unified Allure report, then opens it in your browser.

Order of execution:
1. Functional tests (`functional-tests/`)
2. BDD tests (`bdd-tests/`)
3. UX tests (`ux-tests/`)
4. Contract tests (`contract-tests/`)

```bash
./generate-allure-report.sh
```

### `scenarios_parser.py` / `main.py`

Parses all Behave feature files and generates a MkDocs documentation site with a full scenario catalog, component index, and links to published Allure reports. Used automatically in the `doc_page.yaml` CI workflow to publish the GitHub Pages site.

```bash
python main.py \
  --page-name "RTP Platform QA" \
  --repo-name "rtp-platform-qa" \
  --root-dir .
```

Output: `docs/` directory + `mkdocs.yml` configuration.

---

### `sanitize-allure-results.py`

Strips sensitive values (tokens, secrets) from Allure result files before they are published to GitHub Pages. Run automatically in CI.

```bash
python sanitize-allure-results.py
```

Make scripts executable if needed:

```bash
chmod +x install-requirements.sh generate-allure-report.sh
```
