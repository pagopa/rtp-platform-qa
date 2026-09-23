import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, getStageLabel, getOptions, describeScenarioVUs, ActorCredentials } from '../../utils/utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationTeardown } from '../../utils/teardown-utils.js';

/**
 * @file Activation Stress Test (k6)
 * @description
 * High-throughput activations. Each iteration generates a random debtor fiscal code and
 * posts an activation payload to the configured endpoint. Custom metrics track RPS,
 * success/failure counts, and response time trends. A teardown helper summarizes results
 * at the end.
 *
 * ## Inputs
 * - Environment variables:
 * - `DEBTOR_SERVICE_PROVIDER_ID` (required): Debtor Service Provider identifier used in payloads.
 * - `SCENARIO` (string, optional, default: 'custom'): selects the load profile. One of
 *   `stress_test`, `soak_test`, `spike_test` (arrival-rate based, see `progressiveOptions`
 *   in `utils.js` for the exact ramps/durations), their `_fixed_user` variants (same
 *   ramps/durations but constant-VUs), or `custom` (default) to use the simple
 *   `shared-iterations` executor below, controlled by `VU_COUNT_SET`/`ITERATIONS`/`SLEEP_ITER`.
 * - `VU_COUNT_SET` (number, optional, default: 10): number of virtual users (only used when SCENARIO='custom').
 * - `ITERATIONS` (number, optional, default: 30000): total iterations across all VUs (only used when SCENARIO='custom').
 * - `SLEEP_ITER` (number, seconds, optional, default: 0): sleep after each iteration.
 *
 * ## Behavior
 * - `setup()` authenticates and returns an access token.
 * - `activate()` posts activation requests, collects metrics, and validates 201 responses.
 * - `teardown` and `handleSummary` generate end-of-test artifacts.
 */

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Debtor Service Provider ID from environment (required). */
const DEBTOR_SERVICE_PROVIDER_ID = String(__ENV.DEBTOR_SERVICE_PROVIDER_ID);

/** Number of virtual users. */
const VU_COUNT = Number(__ENV.VU_COUNT_SET) || 10;

/** Total shared iterations for the scenario. */
const ITERATIONS = Number(__ENV.ITERATIONS) || 30000;

/** Optional per-iteration sleep (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** Load profile to use. See file-level doc comment above for the accepted values. */
const SCENARIO = __ENV.SCENARIO || 'custom';

/** Scenario names backed by the predefined ramps/durations in `progressiveOptions` (utils.js). */
const PREDEFINED_SCENARIOS = [
  'stress_test', 'soak_test', 'spike_test',
  'stress_test_fixed_user', 'soak_test_fixed_user', 'spike_test_fixed_user'
];

if (!__ENV.DEBTOR_SERVICE_PROVIDER_ID) {
    throw new Error("❌ DEBTOR_SERVICE_PROVIDER_ID cannot be null or undefined");
}

/**
 * Custom metrics used by the test.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate} currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend} responseTimeTrend
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * Mutable ref object used by teardown/summary helpers to read completion state.
 * @type {{ value: boolean }}
 */
const testCompletedRef = { value: false };

/**
 * k6 options and scenario configuration.
 * - Uses a `shared-iterations` executor and runs the `activate` function.
 *
 * @type {import('k6/options').Options}
 */
export let options = PREDEFINED_SCENARIOS.includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, 'activate'),
      setupTimeout: '5m'
    }
  : {
      ...getOptions('stress_test_fixed_user', 'activate'),
      setupTimeout: '5m',
      scenarios: {
        stress_test_fixed_user: {
          executor: 'shared-iterations',
          vus: VU_COUNT,
          iterations: ITERATIONS,
          maxDuration: '30m',
          gracefulStop: '30m',
          exec: 'activate'
        }
      }
    };

/**
 * @typedef {Object} SetupAuthResult
 * @property {string} access_token OAuth access token.
 */

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER` and returns the resulting token for use
 * in the test function.
 *
 * @returns {SetupAuthResult} Access token wrapper used by `activate()`.
 */
export function setup() {
  return setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
}

/**
 * Test body: performs an activation request with a random debtor fiscal code.
 *
 * - Builds headers with the access token, sets JSON content type.
 * - Constructs the activation payload using `DEBTOR_SERVICE_PROVIDER_ID` and a random fiscal code.
 * - Posts to the activations endpoint and records metrics.
 * - Marks a request as successful only on HTTP 201.
 *
 * @param {SetupAuthResult} data Setup data returned by `setup()`.
 * @returns {import('k6/http').RefinedResponse<'text'>} The HTTP response object.
 */
export function activate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: getStageLabel(SCENARIO, elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const headers = { ...buildHeaders(data.access_token), 'Content-Type': 'application/json' };
  const debtorFiscalCode = randomFiscalCode();

  const payload = {
    payer: {
      fiscalCode: debtorFiscalCode,
      rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const url = endpoints.activations;

  const start = Date.now();
  const res = http.post(url, JSON.stringify(payload), { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 201) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Activation failed — Status ${res.status}, Body: ${res.body}`);
  }

  check(res, {
    'activation: status is 201': (r) => r.status === 201
  });

    if (SLEEP_ITER > 0) {
        sleep(SLEEP_ITER);
    }

  return res;
}

/**
 * k6 `teardown` export produced by the activation-specific teardown factory.
 */
export const teardown = createActivationTeardown({
  START_TIME,
  VU_COUNT,
  testCompletedRef
});

/**
 * k6 `handleSummary` export.
 *
 * Delegates to the shared summary factory, which generates aggregated artifacts
 * and annotates results. `testCompletedRef` is NOT forced to `true` here: it is
 * already set from the real completion signal (`data.allCompleted`) inside
 * `teardown` (see `createActivationTeardown`/`createBatchProcessingTeardown`),
 * which always runs before `handleSummary`. Overriding it here would mark
 * interrupted/partial runs as `COMPLETED` regardless of what actually happened.
 *
 * `activate()` has no batch-tracking signal (unlike deactivation/get-activations),
 * so for the arrival-rate scenarios (stress_test/soak_test/spike_test and their
 * `_fixed_user` variants use a fixed VU count instead, no scenarioConfig needed
 * there) completion is derived from `evaluateArrivalRateCompletion` (schedule vs.
 * actual iterations/duration), NOT from the success/failure ratio — a high failure
 * rate is an expected/legitimate outcome of these tests, not a sign of interruption.
 */
export const handleSummary = (opts) => {
    return createHandleSummary({
        START_TIME,
        testName: 'ACTIVATION STRESS TEST',
        countTag: 'requestCount',
        reportPrefix: 'activation',
        // Arrival-rate scenarios (stress_test/soak_test/spike_test) scale VUs
        // dynamically, so raw VU_COUNT would be misleading in the report;
        // describeScenarioVUs() reports the real allocation for the active SCENARIO.
        VU_COUNT: describeScenarioVUs(SCENARIO, VU_COUNT),
        testCompletedRef,
        scenarioConfig: options.scenarios ? options.scenarios[SCENARIO] : undefined
    })(opts);
};
