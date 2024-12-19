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

### 2. Create a virtual environment

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

### 3. Install specific dependencies for test type

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
