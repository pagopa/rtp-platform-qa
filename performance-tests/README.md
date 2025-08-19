# RTP Platform QA - Performance Tests

This directory contains k6 performance tests and utilities for the RTP Platform.
## Prerequisites
1. Node.js and npm (for optional dependencies)
2. k6 installed ([installation guide](https://k6.io/docs/getting-started/installation))
3. Bash shell (zsh on macOS)
4. A `.env` file at project root with one of the following variables group (depending on the actor that wants to access a given resource):

```ini
DEBTOR_SERVICE_PROVIDER_B_CLIENT_ID=...
DEBTOR_SERVICE_PROVIDER_B_ID=...
DEBTOR_SERVICE_PROVIDER_B_CLIENT_SECRET=...

CREDITOR_SERVICE_PROVIDER_CLIENT_ID=...
CREDITOR_SERVICE_PROVIDER_ID=...
CREDITOR_SERVICE_PROVIDER_CLIENT_SECRET=...

SERVICE_REGISTRY_READER_CLIENT_ID=...
SERVICE_REGISTRY_READER_CLIENT_SECRET=...
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



### General
- `utils/utils.js`: Common helpers such as:
  1. `setupAuth(actor)` – Retrieves access token for a specified actor
  2. `randomFiscalCode()` – Generates a fake fiscal code
  3. `buildHeaders(token)` – Constructs request headers with bearer token
  4. `determineStage(elapsed)` – Determines load stage based on elapsed time
  5. `getOptions(scenario, name)` – Builds test options per scenario

### Batch Utilities
- `utils/batch_utils.js`: Tools for generating and organizing bulk test data:
  1. `createActivationsInBatch(params)` – Creates test activations in batches, supports error handling and retries
  2. `shuffleArray(array)` – Randomizes array elements
  3. `distributeItemsAmongGroups(items, groupCount)` – Evenly partitions an array into N subgroups

### Metrics
- `utils/metrics-utils.js`: Custom k6 metric creation and time-window analysis:
  1. `createStandardMetrics(prefix?)` – Returns standard metric instances (RPS, counters, trends)
  2. `analyzeTimeWindowsData(data)` – Groups metric entries by time buckets
  3. `findBreakingPoint(analysis, failureThreshold)` – Identifies load threshold based on failure rate
  4. `findFirstFailure(analysis)` – Locates first failure point in test
  5. `getMaxTagCount(data, tagName)` – Returns max tag count value
  6. `calculateOverallStats(data, params)` – Computes overall test results (success %, average response, etc.)

### Reporting
- `utils/report-utils.js`: Utility methods for producing formatted textual reports:
  1. `generateTextReport(params)` – Creates a detailed plain-text summary of test execution, metrics, failures, and load patterns
  2. `generateVuStatsText(vuStats, processedKey?)` – Formats per-VU performance stats for inclusion in final report
  3. `generateTeardownInfo(finalState, vuStatsText, testType)` – Produces structured teardown summary including completion rates and durations

### Summary Generation
- `utils/summary-utils.js`: Functions for generating detailed test summaries and handleSummary functions:
  1. `createTestSummary(params)` – Generates a detailed report on the test results, including time windows analysis, breaking point, first failure, and overall statistics.
  2. `createHandleSummary(config)` – Creates a generator for handleSummary functions, allowing for cleaner definition of handleSummary in test files and reducing code duplication.

### Teardown Utilities
- `utils/teardown-utils.js`: Functions for creating teardown functions for batch processing tests:
  1. `createBatchProcessingTeardown(config)` – Creates a standardized teardown function for batch processing tests, such as activation or deactivation tests.
  2. `createDeactivationTeardown(config)` – Creates a specialized teardown function for deactivation tests.
  3. `createActivationTeardown(config)` – Creates a specialized teardown function for activation tests.


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

