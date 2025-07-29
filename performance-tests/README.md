# RTP Platform QA - Performance Tests

This directory contains k6 performance tests and utilities for the RTP Platform.
## Prerequisites
1. Node.js and npm (for k6-reporter if generating HTML reports)
2. k6 installed ([installation guide](https://k6.io/docs/getting-started/installation))
3. Bash shell (zsh on macOS)
4. A `.env` file at project root with the following variables:

```ini
DEBTOR_SERVICE_PROVIDER_CLIENT_ID=...
DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET=...
DEBTOR_SERVICE_PROVIDER_ID=...
For Prometheus output, define `PROM_HOST` and `PROM_PORT`.

5. Python 3 and pip (for post-test analysis):

```bash
pip3 install -r requirements.txt
```

## Directory Structure
```
performance-tests/
    config/
    utils/
    tests/
    run-tests.sh          # Test runner script
    analyze_breaking_point.py # Post-test analysis tool

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
* `<output-format>`: `console`, `dashboard`, `json`, `html`, `prometheus`
* `[scenario]`: `stress_test`, `soak_test`, `spike_test`

### Examples
```bash
# Console output, stress test
./run-tests.sh tests/rtp-activator activation-finder.js console
```
# Launch web dashboard, spike test
./run-tests.sh rtp-activator/activation.js dashboard spike_test

## Post-Test Analysis
Use the Python script to analyze a k6 JSON results file:

```bash
python3 analyze_breaking_point.py results_stress_test_<timestamp>.json
```
This will print summary metrics and generate charts:
* `success_failure_rate.png`
* `response_time_metrics.png`

## Adding New Tests
1. Create a new script in `tests/<service>/`.
2. Import shared logic from `utils/activation_utils.js`:

```javascript
import { setupAuth, randomFiscalCode, config, progressiveOptions } from '../../utils/activation_utils.js';
export let options = progressiveOptions;
export function setup() { return setupAuth(); }
# RTP Platform QA - Performance Tests

This directory contains k6 performance tests and utilities for the RTP Platform.

## Prerequisites
- Node.js and npm (for k6-reporter if generating HTML reports)
- k6 installed (https://k6.io/docs/getting-started/installation)
- Bash shell (zsh on macOS)
- A `.env` file at project root with the following variables:
  ```ini
  DEBTOR_SERVICE_PROVIDER_CLIENT_ID=...
  DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET=...
  DEBTOR_SERVICE_PROVIDER_ID=...
  ```
- (Optional) `PROM_HOST` and `PROM_PORT` for Prometheus output

## Directory Structure
export function activate(data) { /* ... */ }
```
3. Run with `run-tests.sh`.

## Contributing
```
performance-tests/
├── config/
│   └── config.js         # Central URL configuration
├── utils/
│   ├── utility.js        # Generic helpers (auth, payloads)
│   └── activation_utils.js # Auth, option factories, common logic
├── tests/
│   └── rtp-activator/
│       ├── activation-finder.js
│       ├── activation.js
│       └── activation_flow.js
├── run-tests.sh          # Test runner script
└── analyze_breaking_point.py # Post-test analysis tool
```

## Configuration
All service URLs are centralized in `config/config.js`. Secrets and environment-specific values are read from `.env` in the parent folder.

## Utilities
- `utils/utility.js`: Generic functions (e.g. `getValidAccessToken`, common payload generators)
- `utils/activation_utils.js`: Defines:
  - `setupAuth()` for OAuth token retrieval
  - `randomFiscalCode()` for payload generation
  - `commonOptions` and `progressiveOptions` for k6 script options

## Running Tests
Use `run-tests.sh` to execute performance scripts:

```bash
# Basic usage: folder + script + output-format + [scenario]
./run-tests.sh <test-folder> <script.js> <output-format> [scenario]
# Or use direct script path:
./run-tests.sh <folder/script.js> <output-format> [scenario]
```

### Parameters
- `<test-folder>`: e.g. `tests/rtp-activator`
- `<script.js>`: script filename in that folder
- `<output-format>` (required): `console`, `dashboard`, `json`, `html`, `prometheus`
- `[scenario]` (optional): `stress_test`, `soak_test`, `spike_test`

### Examples
```bash
# Console output, stress test
./run-tests.sh tests/rtp-activator activation-finder.js console

# Launch web dashboard, spike test
./run-tests.sh rtp-activator/activation.js dashboard spike_test

# Generate JSON results for soak test
./run-tests.sh tests/rtp-activator activation-finder.js json soak_test

# Generate HTML report
./run-tests.sh tests/rtp-activator activation-finder.js html stress_test
```

## Post-Test Analysis
Use the Python script to analyze a k6 JSON results file:

```bash
python3 analyze_breaking_point.py results_stress_test_<timestamp>.json
```

This will print summary metrics and generate charts:
- `success_failure_rate.png`
- `response_time_metrics.png`

## Adding New Tests
1. Create a new script in `tests/<service>/`.
2. Import shared logic from `utils/activation_utils.js`:
   ```js
   import { setupAuth, randomFiscalCode, config, progressiveOptions } from '../../utils/activation_utils.js';
   export let options = progressiveOptions;
   export function setup() { return setupAuth(); }
   export function activate(data) { /* ... */ }
   ```
3. Run with `run-tests.sh`.

## Contributing
Feel free to extend `config/config.js` for new services, add new payload helpers in `utility.js`, or create additional option factories in `activation_utils.js`. Always update this README with new instructions.
