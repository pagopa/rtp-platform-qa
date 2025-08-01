# RTP Platform QA - Performance Tests

This directory contains k6 performance tests and utilities for the RTP Platform.
## Prerequisites
1. Node.js and npm (for optional dependencies)
2. k6 installed ([installation guide](https://k6.io/docs/getting-started/installation))
3. Bash shell (zsh on macOS)
4. A `.env` file at project root with the following variables:

```ini
DEBTOR_SERVICE_PROVIDER_CLIENT_ID=...
DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET=...
DEBTOR_SERVICE_PROVIDER_ID=...
For Prometheus output, define `PROM_HOST` and `PROM_PORT`.

## Directory Structure
```
performance-tests/
    config/
    utils/
    tests/
    run-tests.sh          # Test runner script

## Configuration
All service URLs are centralized in `config/config.js`. Secrets and environment-specific values are read from `.env` in the parent folder.

## Utilities
* `utils/utility.js`: Generic functions (e.g. `getValidAccessToken`, payload generators)
* `utils/activation_utils.js`: Defines:
  1. `setupAuth()` for OAuth token retrieval
  2. `randomFiscalCode()` for payload generation
  3. `commonOptions` and `progressiveOptions` for k6 script options

## Running Tests
Use `run-tests.sh` to execute performance scripts:

```bash
# Basic usage: folder + script + output-format + [scenario]
./run-tests.sh <test-folder> <script.js> <output-format> [scenario]
```
### Parameters
* `<test-folder>`: e.g. `tests/rtp-activator`
* `<script.js>`: script filename in that folder
* `<output-format>`: `console`, `dashboard`, `json`, `prometheus`
* `[scenario]`: `stress_test`, `soak_test`, `spike_test`, `stress_test_fixed_user`, `soak_test_fixed_user`, `spike_test_fixed_user`

### Examples
```bash
# Console output, stress test
./run-tests.sh tests/rtp-activator activation-finder.js console
```
# Launch web dashboard, spike test
./run-tests.sh rtp-activator/activation.js dashboard spike_test

 # RTP Platform QA - Performance Tests

 This directory contains k6-based performance tests and utilities for the RTP Platform.

 ## Prerequisites


 ## Directory Structure
 ```
 performance-tests/
 ├── config/
 ├── utils/
 ├── tests/
 └──  run-tests.sh             # k6 test runner script
 ```

 ## Configuration
 All service URLs are centralized in `config/config.js`. Environment-specific values are read from `.env` in the parent folder.

 ## Utilities
 - `utils/utility.js`: Auth, token retrieval, payload generators
 - `utils/activation_utils.js`: `setupAuth()`, payload helpers, `commonOptions`, `progressiveOptions`

 ## Running Tests
 Use `run-tests.sh` to execute performance scripts:
 ```bash
 ./run-tests.sh <test-folder> <script.js> <output-format> [scenario]
 ```

 ### Output Formats
 - `console`: Terminal output (default)
 - `dashboard`: Interactive web dashboard at <http://127.0.0.1:5665>
 - `json`: JSON results file
 - `prometheus`: Send metrics to Prometheus server

 ### Scenarios (default: `stress_test`)
 - `stress_test`
 - `soak_test`
 - `spike_test`
 - `stress_test_fixed_user`
 - `soak_test_fixed_user`
 - `spike_test_fixed_user`

 ### Examples
 ```bash
 # Console output, stress test
 ./run-tests.sh tests/rtp-activator activation-finder.js console stress_test

 # Launch web dashboard, spike test
 ./run-tests.sh tests/rtp-activator activation.js dashboard spike_test

 # Generate JSON output
 ./run-tests.sh tests/rtp-activator activation-finder.js json soak_test
 ```

 Generates: `success_failure_rate.png`, `response_time_metrics.png`

 ## Adding New Tests
 1. Create a script in `tests/<service>/`.
 2. Import shared logic:
    ```js
    import { setupAuth, randomFiscalCode, progressiveOptions } from '../utils/activation_utils.js';
    export let options = progressiveOptions;
    export function setup() { return setupAuth(); }
    ```
 3. Run with `run-tests.sh`

 ## Contributing
 Extend `config/config.js`, add helpers in `utility.js`, or add option factories in `activation_utils.js`. Update this README when adding new features.

