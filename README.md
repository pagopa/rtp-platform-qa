# RTP Platform Quality Assurance Repository

This repository contains a comprehensive set of tests for various aspects of the RTP platform, including functional
tests, BDD tests, UX tests, performance tests and fuzz tests. These tests are implemented using Python and appropriate
libraries for each type of testing.

## Table of Contents

- [Setup](#setup)
- [Test Overview](#test-overview)
    - [Functional Tests](#functional-tests)
    - [BDD Tests](#bdd-tests)
    - [UX Tests](#ux-tests)
    - [Performance Tests](#performance-tests)
    - [Fuzz Tests](#fuzz-tests)

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

3. Install local packages:

  ```bash
  pip install -r requirements.txt
  ```

4. Install common dependencies:

  ```bash
  pip install -e .
  ```

### 4. Install specific dependencies for test type

Each test type has its own requirements.txt file. You can install dependencies for individual test types using the
following commands:

#### Functional Tests:

```bash
pip install -r functional-tests/requirements.txt
```

#### BDD Tests:

```bash
pip install -r bdd-tests/requirements.txt
```

#### UX Tests:

```bash
pip install -r ux-tests/requirements.txt
```

#### Performance Tests:

```bash
pip install -r performance-tests/requirements.txt
```

#### Contract Tests:

```bash
pip install -r contract-tests/requirements.txt
```

## Test Overview

### Functional Tests

Functional tests verify the basic functionality of the platform. We use pytest for writing and running these tests.

- Location: functional-tests/
- Tool: pytest
- Configuration: pytest.ini
- Command to run:

```bash
pytest functional-tests/tests/
```

### BDD Tests

BDD (Behavior-Driven Development) tests are written using behave, which allows defining scenarios in Gherkin syntax to
describe user behaviors and expectations.

- Location: bdd-tests/
- Tool: behave
- Feature files: bdd-tests/features/
- Step definitions: bdd-tests/steps/
- Configuration: behave.ini
- Command to run:

```bash
behave bdd-tests/features/
```

### UX Tests

UX tests validate the user experience and interaction flow using Playwright for browser automation.

- Location: ux-tests/
- Tool: Playwright
- Configuration: playwright.config.py
- Command to run:

```bash
pytest ux-tests/tests/
```

### Performance Tests

Performance tests help evaluate how the platform performs under heavy performance or high traffic using Locust.

- Location: performance-tests/
- Tool: Locust
- Configuration: locustfile.py
- Command to run:

```bash
locust -f performance-tests/locustfile.py --headless --users 5 --spawn-rate 1 --run-time 10 --host=http://example.com
```

### Contract Tests

Contract tests use Schemathesis to generate random input values to test the adhesion to OpenAPI specification of the
service.

- Location: contract-tests/
- Tool: Schemathesis
- Command to run:

```bash
pytest contract-tests/*.py --disable-warnings --alluredir allure-results
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


# Run it locally

To run the tests locally you need to set up an .env file in the root project dir with all the vars that you can see above.


## Project Structure

```
├── api/
│   └── __pycache__/
├── bdd-tests/
│   ├── Central Registry/
│   │   └── features/
│   ├── Creditor Service Provider/
│   └── steps/
├── config/
│   └── __pycache__/
├── contract-tests/
├── functional-tests/
│   ├── __pycache__/
│   └── tests/
│       └── __pycache__/
├── performance-tests/
├── rtd_platform_qa.egg-info/
├── utils/
│   └── __pycache__/
└── ux-tests/
    └── tests/
```
