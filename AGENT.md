# AGENT.md

This file provides guidance to AI agents and coding assistants (Claude Code, GitHub Copilot, etc.) when working with this repository.

---

## 1. Project Context

This repository is the **QA test suite for the PagoPA RTP (Request to Pay) platform**, which implements the **SEPA Credit Transfer Instant (SCTInst) Request-to-Pay** standard for the Italian payment ecosystem.

The platform allows a **Creditor Service Provider (CSP)** to send a payment request to a **Debtor Service Provider (DSP)**, which then notifies the debtor (payer). The debtor can accept, reject, or cancel the RTP. All interactions follow SEPA message flows (DS-04 through DS-12).

Key actors:
- **CSP (Creditor Service Provider)**: entity that originates the RTP on behalf of the payee
- **DSP (Debtor Service Provider)**: entity that manages the debtor's bank account and activation
- **PagoPA RTP platform**: central hub routing messages between CSP and DSP
- **Providers**: real banking institutions integrated via API (check `functional-tests/tests/send_rtp/` and `functional-tests/tests/availability/` for the current list; each provider has its own test file and pytest marker)
- **GPD (Gestione Posizioni Debitorie)**: PagoPA debt-position service that feeds RTP creation via Kafka events

---

## 2. Repository Structure

```
rtp-platform-qa/
├── api/                          # HTTP client functions — one file per API domain
│   └── utils/                    # endpoints.py (URLs), http_utils.py (timeout, headers)
├── bdd-tests/                    # Behave BDD tests (Gherkin scenarios)
│   ├── features/                 # .feature files grouped by actor
│   └── steps/                    # Step definitions
├── config/                       # Dynaconf configuration loader
│   └── configuration.py          # Exposes `config` object
├── contract-tests/               # Schemathesis OpenAPI contract tests
├── functional-tests/tests/       # Main pytest integration test suite
│   ├── activation/               # Debtor activation / deactivation / takeover
│   ├── auth/                     # OAuth2 token tests
│   ├── availability/             # Health-check tests per provider
│   ├── callbacks/                # SEPA callback flow tests (DS-04…DS-12)
│   ├── cancel_rtp/               # RTP cancellation
│   ├── get_rtp/                  # RTP retrieval and delivery status
│   ├── gpd_availability/         # GPD service health
│   ├── process_messages_sender/  # GPD Kafka → RTP creation pipeline
│   ├── send_rtp/                 # RTP send per provider (Mock, CBI, Poste, ICCREA)
│   ├── service_registry/         # Payee registry and service provider registry
│   ├── takeover/                 # Debtor takeover scenarios
│   └── conftest.py               # Shared fixtures (tokens, activation factory)
├── gpd-test/tests/               # Standalone GPD debt-position tests
├── load-tests/                   # k6 load test scripts (JavaScript)
├── performance-tests/            # k6 performance test scripts (JavaScript)
├── ux-tests/tests/               # Playwright browser automation tests
├── utils/                        # Shared utilities (40+ modules)
├── config.yaml                   # Non-secret configuration (URLs, timeouts)
├── pyproject.toml                # Project metadata, dependencies, pytest config
├── Makefile                      # Install and run targets
├── .pre-commit-config.yaml       # Ruff linting + formatting hooks
├── sanitize-allure-results.py    # Strip tokens (Bearer, JWT, Auth headers) from Allure JSON
└── generate-allure-report.sh     # Local full-suite report generation
```

---

## 3. Test Suites

| Suite | Location | Framework | Run command |
|-------|----------|-----------|-------------|
| Functional | `functional-tests/tests/` | pytest + allure-pytest | `make test-functional` |
| BDD | `bdd-tests/` | Behave + allure-behave | `make test-bdd` |
| UX | `ux-tests/tests/` | pytest + Playwright | `make test-ux` |
| Contract | `contract-tests/` | Schemathesis + pytest | `make test-contract` |
| GPD | `gpd-test/tests/` | pytest | `pytest gpd-test/tests/` |
| Performance | `performance-tests/` | k6 (JavaScript) | `k6 run ...` |
| Load | `load-tests/` | k6 (JavaScript) | `k6 run ...` |

### Functional test directory layout

Each subdirectory under `functional-tests/tests/` maps to one **platform feature**. Always `ls functional-tests/tests/` to see the current list — new feature directories are added as the platform grows.

Key directories and their purpose:
- `activation/` — CRUD for debtor activation records
- `callbacks/` — SEPA callback flow tests (DS-04 through DS-12)
- `process_messages_sender/` — GPD Kafka event → RTP creation pipeline
- `send_rtp/` — RTP send per provider (one test file per provider)
- `cancel_rtp/` — RTP cancellation scenarios
- `get_rtp/` — RTP retrieval and delivery status
- `availability/` — Health checks per provider (one test file per provider)
- `service_registry/` — Payee and service provider registries
- `takeover/` — Debtor account takeover

---

## 4. Configuration Management

### Split between config.yaml and .env

- **`config.yaml`** — non-secret settings: API base URLs, path suffixes, timeouts (`default_timeout: 5000`, `long_timeout: 60000`). Commit freely.
- **`.env`** — secrets only: client IDs, client secrets, PFX certificates (base64), fiscal codes, subscription keys. Never commit.

### Accessing configuration

```python
from config.configuration import config

url = config.activation_base_url_path + config.activation_path
timeout = config.default_timeout
```

All endpoint URLs are pre-built as constants in `api/utils/endpoints.py`. **Always import from there** — do not construct URLs inline in tests or API clients.

### Secrets (from .env / GitHub Actions secrets)

Secrets follow the naming convention `<ROLE>_CLIENT_ID` / `<ROLE>_CLIENT_SECRET` for OAuth2 credentials, and descriptive names for certificates and keys.

Check `config/configuration.py` for the full list of `os.getenv()` calls — this is the source of truth for required environment variables. Common categories:
- **OAuth2 credentials** — one pair per service provider role (DSP A, DSP B, CSP, RTP Consumer, registries)
- **PFX certificates** — base64-encoded certificates with passwords for mTLS providers
- **API keys** — subscription keys for GPD and other external services
- **Fiscal codes** — organization fiscal codes for test data

---

## 5. API Layer (`api/`)

Each file in `api/` is an HTTP client for one API domain. Functions follow this signature:

```python
def <verb>_<resource>(access_token: str, ...) -> requests.Response:
    return requests.post(
        url=ENDPOINT_CONSTANT,
        headers={"Authorization": access_token, ...},
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
```

Rules:
- **Return the raw `requests.Response`** — never assert inside API functions
- **Always use named arguments** for calls with more than one parameter
- **Always import URL constants from `api/utils/endpoints.py`**
- **Always use `HTTP_TIMEOUT` from `api/utils/http_utils.py`** — never hardcode a timeout value
- **Never add retry logic** inside API functions — retries belong in test fixtures or utilities

**Always `ls api/` to see all current clients.** Each file covers one API domain. Naming convention: `<resource>_api.py` or `<RESOURCE>_<action>_api.py`.

When adding a new provider or endpoint, check if an existing client file already covers that domain before creating a new one.

---

## 6. Utilities Layer (`utils/`)

**Always search `utils/` before writing any new helper.** The directory grows as the platform evolves — `ls utils/` for the full current list.

Modules are organized by category:

### Data generation
- `dataset_*.py` — payload factories (RTP data, EPC data, GPD messages, debt positions, callback scenarios per DS code)
- `fiscal_code_utils.py` — `fake_fc()` for random Italian fiscal codes
- `generators_utils.py` — `generate_iuv()`, `generate_iupd()`, `generate_notice_number()`
- `text_utils.py` — `generate_random_description()`, `generate_transaction_id()`
- `datetime_utils.py` — `generate_expiry_date()`, date parsing
- `iban_utils.py` — IBAN validation and generation
- `idempotency_key_utils.py` — `generate_idempotency_key(operation_slug, resource_id)`

### Assertions and expectations
- `response_assertions_utils.py` — `assert_response_code()`, `assert_body_presence()`
- `test_expectations.py` — expected HTTP status codes per scenario (CREATE/UPDATE/DELETE maps)

### Crypto and auth
- `cryptography_utils.py` — `pfx_to_pem()`, `client_credentials_to_auth_token()`
- `log_sanitizer_helper.py` — `sanitize_bearer_token()` — strip tokens from log strings

### Helpers and constants
- `activation_helpers.py` — pre-built activation flows
- `callback_builder.py` — builder for SEPA callback payloads
- `http_utils.py` — `extract_id_from_location()` from Location header
- `extract_next_activation_id.py` — parse cursor from paginated responses
- `regex_utils.py` — `uuidv4_pattern` for UUID validation
- `type_utils.py` — `JsonType` TypeAlias for JSON structures
- `constants_*.py` — config, secrets, and text constants

### API-internal utilities (`api/utils/`)

| Module | Purpose |
|--------|---------|
| `endpoints.py` | All URL constants — **source of truth** for endpoint paths |
| `http_utils.py` | `HTTP_TIMEOUT`, `APPLICATION_JSON_HEADER`, `CERT_PATH`, `KEY_PATH` |

---

## 7. Shared Fixtures (`functional-tests/tests/conftest.py`)

**Always read `functional-tests/tests/conftest.py` to see all current fixtures.** New token types and utility fixtures are added as the platform integrates more service providers.

### Token fixtures (function-scoped)

All token fixtures call the appropriate OAuth2 endpoint and return a ready-to-use `"Bearer <token>"` string. The naming convention is `<role>_token_<variant>` or `<service>_access_token`.

When a new service provider or role is integrated, add the corresponding token fixture here following the same pattern.

### Utility fixtures

The root conftest also provides factory fixtures for creating test resources:
- **Activation factories** — create fresh debtor activations per call
- **Data generators** — random fiscal codes, cursors for pagination
- **Certificate fixtures** — PFX cert/key pairs for mTLS tests

### Domain-scoped conftest files

Some feature directories under `functional-tests/tests/` have their own `conftest.py` with domain-specific fixtures (e.g. `gpd_availability/conftest.py` for parametrized environment setup). Check each feature directory for local fixtures before adding new ones to the root conftest.

---

## 8. Strict Rules (Mandatory)

### Code Reuse — Search First

Before writing **any** new code:
1. Search `utils/` for an existing helper
2. Search `api/` for an existing API client function
3. Search `functional-tests/tests/conftest.py` for existing fixtures
4. Search `api/utils/endpoints.py` for the URL constant
5. Only write new code when nothing equivalent exists

**Never duplicate logic.** Extract to the appropriate shared module.

### Python Style

- **No linter suppressions** — never add `# noqa`, `# type: ignore`. Fix the code.
- **Absolute imports only** — `from utils.generators_utils import generate_iuv`, never `from ..utils import ...`
- **Named arguments** for all calls with more than one argument
- **No single-letter variable names** — use descriptive names
- **No `time.sleep()`** in test code
- **`conftest.py` is for fixtures only** — helpers and utilities go in `utils/` or a local `utils.py`
- **Test files** contain only test functions and classes — no helper logic inline
- **Imports always at module top** — never inside functions

### Pytest Rules

- **Every new test MUST have at least one marker** — check `pyproject.toml` `[tool.pytest.ini_options] markers` for the list. Never commit an unmarked test.
- **Required markers per test**: at minimum `happy_path` or `unhappy_path`, plus the relevant domain marker (`send`, `activation`, `callback`, `cancel`, `get`, `debt_positions`, etc.)
- **Each test validates one scenario only** — do not bundle multiple behaviors in one test function
- **Use `@pytest.mark.usefixtures`** when the fixture return value is not used in the test body
- **No `pytest.skip()` or `@pytest.mark.skip`** — if a test is known-broken, mark it `@pytest.mark.need_fix` with a comment explaining why
- **Allure decorators required** on every test: `@allure.epic(...)`, `@allure.feature(...)`, `@allure.story(...)` at minimum

### Fixture Rules

- **Single responsibility** — one fixture does one thing
- **Naming**: use NOUNS (what the fixture provides), never verbs
  - ✅ `activated_debtor`, `rtp_payload`, `debtor_service_provider_token_a`
  - ❌ `create_debtor`, `setup_rtp`, `get_token`
- **Cleanup via `yield`** — always use `yield` with teardown code in fixtures that create resources
- **Scope**: use the narrowest scope that works; prefer `function` scope unless setup is expensive

### Assertions

- **Always include a failure message**: `assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"`
- **Use `assert_response_code()` from `utils/response_assertions_utils.py`** when available instead of raw assertions
- **Never assert inside API client functions** — assertions belong only in test functions

### Security

- **Never log or print tokens, secrets, or fiscal codes** in test output
- All `pytest_runtest_makereport` hooks in conftest call `sanitize_bearer_token()` — do not bypass this
- `sanitize-allure-results.py` strips Bearer tokens, JWT tokens (`eyJ...`), and Authorization headers from Allure JSON — always run before publishing reports

### Defensive Programming — Prohibited

Do not add defensive checks for things that are architecturally guaranteed.

❌ **Checking attributes that are always present:**
```python
# WRONG — requests.Response always has status_code
if res is not None and hasattr(res, "status_code"):
    assert res.status_code == 201
```
✅ **Trust the contract:**
```python
assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
```

❌ **Checking config values that Dynaconf always provides:**
```python
# WRONG — if the key is missing, Dynaconf raises a clear error
url = config.get("activation_base_url_path") or "http://fallback"
```
✅ **Access directly:**
```python
url = config.activation_base_url_path
```

❌ **Silencing API errors with try/except:**
```python
# WRONG — hides the real failure
try:
    res = send_rtp(access_token=token, rtp_payload=data)
except Exception:
    pass
```
✅ **Let it fail with a clear message:**
```python
res = send_rtp(access_token=token, rtp_payload=data)
assert res.status_code == 201, f"send_rtp failed: {res.status_code} {res.text}"
```

### Pre-commit — No Exceptions

```bash
pre-commit run --all-files
```

**This MUST pass before every commit. No exceptions.**
- ❌ Never use `git commit --no-verify`
- ❌ Never suppress ruff errors with `# noqa` to make the check pass
- ✅ Fix the code until the check passes

---

## 9. Adding a New Functional Test

Follow this checklist:

1. **Identify the feature directory** — find the matching subdirectory under `functional-tests/tests/`, e.g. `send_rtp/` for a new send scenario. If none exists, create a new directory with an `__init__.py`.

2. **Check `utils/` for existing helpers** — especially `dataset_RTP_data.py`, `generators_utils.py`, `fiscal_code_utils.py`.

3. **Check `api/`** — use the existing API client. If the endpoint is new, add a function to the appropriate `api/` file (never write `requests.post()` directly in test code).

4. **Use shared fixtures** — import from `conftest.py` at the appropriate level. If you need a new fixture shared across multiple test files in the same feature, add it to the local `conftest.py`.

5. **Name the test file** — `test_<functionality>.py` format.

6. **Add Allure decorators and pytest markers** to every test function.

7. **Run pre-commit before committing**:
   ```bash
   pre-commit run --all-files
   ```

### Minimal test template

```python
import allure
import pytest

from api.RTP_send_api import send_rtp
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic("Send RTP")
@allure.feature("Send RTP")
@allure.story("Happy path — send RTP via Mock")
@pytest.mark.happy_path
@pytest.mark.send
@pytest.mark.mock
def test_send_rtp_mock_returns_201(
    creditor_service_provider_token_a: str,
) -> None:
    rtp_data = generate_rtp_data()
    res = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
```

---

## 10. Adding a New API Client Function

1. Identify the correct file in `api/` (or create a new file if the domain is entirely new).
2. Import URL from `api/utils/endpoints.py` — add the constant there if it doesn't exist.
3. Import `HTTP_TIMEOUT` and any header constants from `api/utils/http_utils.py`.
4. Return the raw `requests.Response`.
5. Use named arguments in the `requests.*` call.

```python
from api.utils.endpoints import NEW_ENDPOINT_URL
from api.utils.http_utils import HTTP_TIMEOUT


def cancel_rtp(access_token: str, rtp_id: str) -> requests.Response:
    return requests.post(
        url=f"{NEW_ENDPOINT_URL}/{rtp_id}/cancel",
        headers={"Authorization": access_token, "Content-Type": "application/json"},
        timeout=HTTP_TIMEOUT,
    )
```

---

## 11. SEPA Callback Flow Reference

The callback test files correspond directly to SEPA DS (Data Set) message types:

| DS code | Meaning | Test file prefix |
|---------|---------|-----------------|
| DS-04 | Payment request sent (PEND) | `test_RTP_callback_DS_04` |
| DS-05 | Synchronous acceptance (ACTC) | `test_RTP_callback_DS_05` |
| DS-08 | Positive (ACCP, ACWC, RJCT) and negative responses | `test_RTP_callback_DS_08` |
| DS-12P | Cancellation notification | `test_RTP_callback_DS_12P` |
| DS-12N | Refusal | `test_RTP_callback_DS_12N` |

Status transitions:
```
CREATED → SENT → PEND → ACTC → ACCP → ACSC (paid)
                              → ACWC → CNCL (creditor cancelled)
                              → RJCT        (debtor rejected)
```

---

## 12. GPD Pipeline Reference

The `process_messages_sender/` tests exercise the pipeline:
```
GPD Kafka event → rtp-consumer → rtp-sender → RTP created/updated/deleted
```

- **CREATE message** → new RTP created for the debt position
- **UPDATE message** → existing RTP status updated (e.g. PAID, EXPIRED)
- **DELETE message** → RTP cancelled
- **UPDATE before CREATE** — edge case: UPDATE arrives before CREATE is processed

The `psp_tax_code` in the GPD message determines which provider processes the RTP (Mock04-tax-code → mock provider).

Dataset factories are in `utils/dataset_gpd_message.py`. Expected HTTP status codes per scenario are in `utils/test_expectations.py`.

---

## 13. CI/CD Pipeline

### run_tests.yml — main workflow

Triggered on: push to `main`, daily at 06:00 UTC, manual `workflow_dispatch`.

Job execution order (sequential):
1. **Functional_Tests** → pytest `functional-tests/tests/`
2. **BDD_Tests** → behave `bdd-tests/features`
3. **UX_Tests** → pytest `ux-tests/tests/`
4. **Contract_Tests** → pytest `contract-tests/`
5. **Aggregate_Results** → merges Allure artifacts, sanitizes, publishes to gh-pages

Each job:
- Uses GitHub environment **UAT**
- Runs with secrets injected as environment variables
- Uploads `allure-results/` as artifact
- Sanitizes results with `sanitize-allure-results.py` before upload

### Other workflows

`ls .github/workflows/` to see all current workflows. Besides `run_tests.yml`, common workflows include:
- Manual test execution workflows (GPD, specific suites)
- Allure fail rate extraction and Slack notifications
- Docker image publishing
- Documentation deployment to gh-pages

---

## 14. Failure Analysis

When a test fails, follow this decision order:

### Step 1 — Read the test code first

Before any classification, read:
1. The failing test function
2. The fixtures it uses (local `conftest.py` + root `conftest.py`)
3. The API client function called
4. Any utility functions in the call chain

Never classify based on error messages alone.

### Step 2 — Identify the failure type

**Test/code issue** — fix in this repo:
- `AssertionError` with wrong expected status code → check `utils/test_expectations.py` for correct expected codes
- Token fixture fails (401/403) → OAuth2 configuration or secret mismatch
- `KeyError` on response body field → API response schema changed or wrong field name
- `requests.exceptions.ConnectionError` or `Timeout` → environment issue or `config.yaml` URL wrong
- Import error → missing dependency or wrong import path
- Fixture setup fails → check fixture chain in conftest

**Platform/integration issue** — file a bug against the backend service:
- Valid request returns unexpected 4xx/5xx consistently
- RTP stuck in wrong status after valid operation
- Callback not received after correct RTP creation
- GPD message not triggering expected RTP lifecycle change

**Environment issue** — not a code bug:
- Test environment UAT unreachable
- Keycloak token endpoint down
- External provider unavailable (check `functional-tests/tests/availability/` for current providers)
- Expired certificates or rotated secrets in GitHub environment

### Step 3 — Classify the marker

- `happy_path` test fails → usually platform issue or environment
- `unhappy_path` test fails → usually test expectation wrong (check `test_expectations.py`)
- `need_fix` marked test fails → already known, do not re-investigate unless fixing

### Common failure patterns

| Pattern | Most likely cause |
|---------|------------------|
| `assert res.status_code == X, got Y` | Wrong expected code in test or API behavior changed |
| `KeyError: 'activationId'` | Response schema changed or fixture didn't create the resource |
| `401 Unauthorized` | Token expired mid-run or secret not set in environment |
| `ConnectionError` to `api-rtp.uat.cstar.pagopa.it` | UAT environment down |
| `AssertionError` in `process_messages_sender` test | GPD pipeline delay; check `long_timeout` config |
| BDD `StepError` on `the debtor A is activated` | `activate_with_sp_a()` returned non-201; check activation service |

---

## 15. PR Test Recommendations

When reviewing a PR, recommend tests based on what was changed. Use these general rules:

### By changed area

| Changed area | Strategy |
|-------------|----------|
| `api/<domain>_api.py` | Run `pytest -m <matching_marker>` — the marker matches the domain name (e.g. `activation`, `send`, `cancel`, `callback`, `get`) |
| `utils/dataset_*.py` | Run tests for the domain that consumes that dataset (e.g. callback dataset → `-m callback`) |
| `utils/test_expectations.py` | Run all suites that validate HTTP status codes against these maps |
| `utils/fiscal_code_utils.py` | Run `-m activation` (primary consumer) |
| `utils/cryptography_utils.py` | Run `-m mock` (mTLS tests) |
| `functional-tests/tests/conftest.py` | Full functional suite |
| `config/configuration.py` or `config.yaml` | Full functional suite (config affects all tests) |
| `bdd-tests/steps/` | Full BDD suite (`make test-bdd`) |
| `ux-tests/` | UX suite (`make test-ux`) |
| `contract-tests/` | Contract suite (`make test-contract`) |

### How to find the right marker

Each API domain has a corresponding pytest marker defined in `pyproject.toml`. When a new provider or domain is added, a new marker is registered there. Always check `pyproject.toml` `[tool.pytest.ini_options] markers` for the current list.

### What NOT to recommend

- Do NOT recommend `gpd-test/` for general changes — it requires a running GPD environment and is triggered separately via a manual workflow.
- Do NOT recommend provider-specific tests (e.g. `-m cbi`) when the change is provider-agnostic — use the domain marker instead (e.g. `-m send`).

---

## 16. Anti-Patterns

These are the most common mistakes in this codebase. Each one has caused bugs or maintenance problems before.

### ❌ Writing HTTP calls directly in test files

```python
# WRONG — raw requests call belongs in api/, not in a test
def test_send_rtp(creditor_service_provider_token_a):
    res = requests.post(
        url="https://api-rtp.uat.cstar.pagopa.it/rtp/v1/rtps",
        headers={"Authorization": creditor_service_provider_token_a},
        json={"amount": 100},
        timeout=5000,
    )
    assert res.status_code == 201
```
✅ Use the existing client from `api/`:
```python
from api.RTP_send_api import send_rtp
from utils.dataset_RTP_data import generate_rtp_data

def test_send_rtp(creditor_service_provider_token_a):
    res = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=generate_rtp_data())
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
```

---

### ❌ Calling `res.json()` without checking status code first

```python
# WRONG — if the response is a 4xx/5xx, .json() may raise or return an error body
body = res.json()
assert body["activationId"] == expected_id
```
✅ Always check status code before accessing the body:
```python
assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
body = res.json()
assert body["activationId"] == expected_id
```

---

### ❌ Hardcoding expected HTTP status codes instead of using `test_expectations.py`

```python
# WRONG — the expected code for this scenario is already defined centrally
assert res.status_code == 200
```
✅ If the scenario is in `utils/test_expectations.py`, import from there:
```python
from utils.test_expectations import UPDATE_EXPECTED_CODES

assert res.status_code == UPDATE_EXPECTED_CODES[psp_tax_code]
```

---

### ❌ Constructing URLs inline instead of using `api/utils/endpoints.py`

```python
# WRONG — URL duplicated, breaks if config changes
url = config.activation_base_url_path + "/api/v1/activations"
```
✅ Import the pre-built constant:
```python
from api.utils.endpoints import ACTIVATION_URL

res = requests.get(url=ACTIVATION_URL, ...)
```

---

### ❌ Putting helper functions in `conftest.py` or test files

```python
# WRONG — conftest.py is for fixtures only
# functional-tests/tests/conftest.py
def build_activation_payload(fiscal_code: str) -> dict:
    return {"fiscalCode": fiscal_code, ...}
```
✅ Put helpers in `utils/` (shared) or a local `utils.py` (feature-specific):
```python
# utils/activation_helpers.py  ← if used across features
# functional-tests/tests/activation/utils.py  ← if local to activation
def build_activation_payload(fiscal_code: str) -> dict:
    return {"fiscalCode": fiscal_code, ...}
```

---

### ❌ Calling token functions directly in tests instead of using fixtures

```python
# WRONG — bypasses fixture lifecycle, token not sanitized from logs
def test_something():
    token = get_keycloak_access_token(
        client_id=os.getenv("DSP_A_CLIENT_ID"),
        client_secret=os.getenv("DSP_A_CLIENT_SECRET"),
    )
    ...
```
✅ Declare the fixture as a parameter:
```python
def test_something(debtor_service_provider_token_a: str) -> None:
    ...
```

---

### ❌ Bundling multiple scenarios in one test function

```python
# WRONG — if the first assertion fails, the rest don't run; root cause is harder to diagnose
def test_activation_flows(make_activation, debtor_service_provider_token_a):
    # scenario 1: create
    activation_id, fc = make_activation()
    assert activation_id is not None

    # scenario 2: get
    res = get_activation(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 200

    # scenario 3: deactivate
    res = deactivate(debtor_service_provider_token_a, activation_id)
    assert res.status_code == 204
```
✅ One function, one scenario:
```python
def test_create_activation_returns_activation_id(make_activation): ...
def test_get_activation_returns_200(activated_debtor, debtor_service_provider_token_a): ...
def test_deactivate_returns_204(activated_debtor, debtor_service_provider_token_a): ...
```

---

### ❌ Using `time.sleep()` to wait for async side effects

```python
# WRONG — arbitrary sleep is fragile: too short on slow CI, too long locally
res = send_rtp(access_token=token, rtp_payload=data)
time.sleep(5)
status_res = get_rtp(access_token=token, rtp_id=rtp_id)
assert status_res.json()["status"] == "PEND"
```
✅ Poll with a timeout loop using a short sleep and a deadline:
```python
import time

deadline = time.time() + 30
while time.time() < deadline:
    status_res = get_rtp(access_token=token, rtp_id=rtp_id)
    if status_res.status_code == 200 and status_res.json().get("status") == "PEND":
        break
    time.sleep(2)
else:
    raise AssertionError(f"RTP never reached PEND status: {status_res.text}")
```

---

### ❌ Writing a new fiscal code generator when `fake_fc()` exists

```python
# WRONG — reinventing existing utility
import random, string
fc = "".join(random.choices(string.ascii_uppercase, k=16))
```
✅ Use the existing utility:
```python
from utils.fiscal_code_utils import fake_fc

fc = fake_fc()
```

---

### ❌ Missing Allure decorators on a test function

```python
# WRONG — test appears in Allure with no metadata, impossible to filter or understand
@pytest.mark.happy_path
@pytest.mark.send
def test_send_rtp_mock(creditor_service_provider_token_a): ...
```
✅ Always add at minimum `epic`, `feature`, `story`:
```python
@allure.epic("Send RTP")
@allure.feature("Send RTP")
@allure.story("Happy path — send RTP via Mock provider")
@pytest.mark.happy_path
@pytest.mark.send
@pytest.mark.mock
def test_send_rtp_mock(creditor_service_provider_token_a: str) -> None: ...
```

---

## 17. Test Isolation Rules

Tests MUST be fully independent. A test failure must never cause another test to fail due to shared state.

- **Each test must create its own resources via fixtures.** Do not rely on resources created by a previous test.
- **Never store state in module-level or class-level variables** to share between tests.
- **Use `function` scope for fixtures that create or modify platform state** (activations, RTPs, debt positions).
- **Cleanup must happen in the fixture, not in the test.** Use `yield` + teardown in the fixture so cleanup runs even when the test fails.
- **Token fixtures are function-scoped by design** — do not promote them to `session` or `module` scope; tokens can expire mid-suite and each test needs a fresh one.
- **Tests in `process_messages_sender/` are an explicit exception**: some depend on ordering due to the GPD pipeline's async nature. When ordering is needed, document it with a comment explaining why.

---

## 18. Idempotency Key Guidance

Several endpoints require an `Idempotency-Key` header to prevent duplicate processing on retry.

- Use `generate_idempotency_key()` from `utils/idempotency_key_utils.py`
- Generate a **new key per test run** — never reuse an idempotency key across test invocations
- Do not hardcode idempotency keys as string literals in test code

```python
from utils.idempotency_key_utils import generate_idempotency_key

headers = {
    "Authorization": token,
    "Idempotency-Key": generate_idempotency_key(
        operation_slug="send_rtp",
        resource_id=rtp_id,
    ),
}
```
