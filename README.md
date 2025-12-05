# RTP Platform Quality Assurance Repository

This repository contains a comprehensive set of tests for various aspects of the RTP platform, including functional
tests, BDD tests, UX tests, performance tests, contract tests. These tests are implemented using Python and appropriate
libraries for each type of testing.

## Table of Contents

- [Setup](#setup)
- [Test Overview](#test-overview)
    - [Functional Tests](#functional-tests)
    - [BDD Tests](#bdd-tests)
    - [UX Tests](#ux-tests)
    - [Performance Tests](#performance-tests)
    - [Contract Tests](#contract-tests)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/platform-testing-repo.git
cd platform-testing-repo
```

### 2. Get secrets

Obtain `secrets.yaml` file (based on `config/secrets_template.yaml`) from admins and place it under `config/`.

### 3. Create a virtual environment

It's recommended to use a virtual environment to manage dependencies.

1. Create virtual environment:

  ```bash
  python3 -m venv .venv
  ```

2. Activate the virtual environment:

  ```bash
  source .venv/bin/activate
  ```

3. Upgrade pip:

  ```bash
  pip install --upgrade pip
  ```

4. Install local packages:

  ```bash
  pip install -e .
  ```

### 4. Install specific dependencies for test type

Dependencies are managed via `pyproject.toml` extras. Use the Makefile for installation:

#### Functional Tests:

```bash
make install-functional
```

#### BDD Tests:

```bash
make install-bdd
```

#### UX Tests:

```bash
make install-ux
```

#### Performance Tests:

```bash
make install-performance
```

#### Contract Tests:

```bash
make install-contract
```

#### End-to-End Tests:

```bash
make install-end-to-end
```

## Test Overview

### Functional Tests

Functional tests verify the basic functionality of the platform. We use pytest for writing and running these tests.

- Location: functional-tests/
- Tool: pytest
- Configuration: pyproject.toml
- Command to run:

```bash
make test-functional
```

### BDD Tests

BDD (Behavior-Driven Development) tests are written using Behave, with scenarios in Gherkin syntax to describe the expected behaviors.

- Location: `bdd-tests/`
- Tool: Behave
- Feature files: `bdd-tests/features/`
- Step definitions: `bdd-tests/steps/`
- Configurazione condivisa: `bdd-tests/environment.py`
- Command to run:

```bash
make test-bdd
or
behave bdd-tests
```

### UX Tests

UX tests validate the user experience and interaction flow using Playwright for browser automation.

- Location: ux-tests/
- Tool: Playwright
- Configuration: playwright.config.py
- Command to run:

```bash
make test-ux
```

### Performance Tests

Performance tests help evaluate how the platform performs under heavy performance or high traffic using k6.

- Location: performance-tests/
- Tool: k6
- Configuration: JavaScript test files under `performance-tests/` and shared utilities in `performance-tests/utils/`
- Command to run (via helper script):

```bash
cd performance-tests
./run-tests.sh tests/rtp-activator activation-finder.js console
```

### Contract Tests

Contract tests use Schemathesis to generate random input values to test the adhesion to OpenAPI specification of the
service.

- Location: contract-tests/
- Tool: Schemathesis
- Command to run:

```bash
make test-contract
```

## Secrets Management on GitHub
GitHub actions uses a repository environments variables that are used by the config to settle up a configuration dictionary.
All the envs and secrets are inside the repository's environment section under env vars and secret.
For each environment we have to specify all the variables:
dev, uat and prod.
For now we are going to use just the UAT env.

This secret must be updated manually by admins when needed.


[Link to env var setting section](https://github.com/pagopa/rtp-platform-qa/settings/environments)


### Debtor Service Provider
`DEBTOR_SERVICE_PROVIDER_CLIENT_ID` - Client ID for authenticating with the primary debtor service provider  
`DEBTOR_SERVICE_PROVIDER_ID` - Unique identifier for the primary debtor service provider  
`DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET` - Secret key for secure authentication with the primary debtor service provider  

### Debtor Service Provider B
`DEBTOR_SERVICE_PROVIDER_B_CLIENT_ID` - Client ID for authenticating with the secondary debtor service provider  
`DEBTOR_SERVICE_PROVIDER_B_ID` - Unique identifier for the secondary debtor service provider  
`DEBTOR_SERVICE_PROVIDER_B_CLIENT_SECRET` - Secret key for secure authentication with the secondary debtor service provider  

### Creditor Service Provider
`CREDITOR_SERVICE_PROVIDER_CLIENT_ID` - Client ID for authenticating with the creditor service provider  
`CREDITOR_SERVICE_PROVIDER_ID` - Unique identifier for the creditor service provider  
`CREDITOR_SERVICE_PROVIDER_CLIENT_SECRET` - Secret key for secure authentication with the creditor service provider  

### PagoPA Integration
`PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_ID` - Client ID for accessing PagoPA payee registry services  
`PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_SECRET` - Secret key for authenticating with PagoPA payee registry  

`PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_ID` - Client ID for accessing PagoPA service registry  
`PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_SECRET` - Secret key for authenticating with PagoPA service registry  

### RTP Reader
`RTP_READER_CLIENT_ID` - Client ID for RTP Reader service authentication
`RTP_READER_CLIENT_SECRET` - Secret key for RTP Reader service authentication

### Webpage Authentication
`WEBPAGE_USERNAME` - Username for web application login authentication  
`WEBPAGE_PASSWORD` - Password for web application login authentication  

### CBI Configuration
`CBI_CLIENT_ID` - Client ID for CBI (Customer to Business Interaction) service authentication  
`CBI_CLIENT_SECRET` - Secret key for CBI service authentication  
`CBI_CLIENT_PFX_BASE64` - Base64 encoded PFX certificate for CBI client authentication  
`CBI_CLIENT_PFX_PASSWORD_BASE64` - Base64 encoded password for the CBI PFX certificate  
`CBI_ACTIVATED_FISCAL_CODE` - Fiscal code for activated CBI services  
`CBI_PAYEE_ID`- CBI payee ID
`CREDITOR_AGENT_ID`- Creditor agent ID

### Mock Service Provider Configuration
`DEBTOR_SERVICE_PROVIDER_MOCK_PFX_BASE64` - Base64 encoded PFX certificate for mock debtor service provider testing  
`DEBTOR_SERVICE_PROVIDER_MOCK_PFX_PASSWORD_BASE64` - Base64 encoded password for the mock debtor service provider PFX certificate  

### Poste Configuration
`POSTE_ACTIVATED_FISCAL_CODE` - Fiscal code for activated Poste Italiane services

### Iccrea Configuration
`ICCREA_ACTIVATED_FISCAL_CODE` - Fiscal code for activated ICCREA services

### DEBT POSITION
`DEBT_POSITIONS_SUBSCRIPTION_KEY` - GPD subscription key
`DEBT_POSITIONS_ORGANIZATION_ID`  - GPD organization ID
`DEBT_POSITIONS_DEV_SUBSCRIPTION_KEY` - GPD subscription key in DEV environment
`DEBT_POSITIONS_DEV_ORGANIZATION_ID` - GPD organization ID in DEV environment

# Run it locally

To run the tests locally you need to set up an .env file in the root project dir with all the vars that you can see above.


## Project Structure

```text
├── api/
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
├── contract-tests/
│   └── tests/
├── functional-tests/
│   └── tests/
├── performance-tests/
├── ux-tests/
│   └── tests/
└── end-to-end-test/
    └── tests/
```
