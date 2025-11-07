import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials } from '../../utils/utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationTeardown } from '../../utils/teardown-utils.js';

/**
 * @file Activation Stress Test (k6)
 * @description
 * High-throughput activations using a shared-iterations scenario. Each iteration generates
 * a random debtor fiscal code and posts an activation payload to the configured endpoint.
 * Custom metrics track RPS, success/failure counts, and response time trends. The run can
 * optionally sleep between iterations. A teardown helper summarizes results at the end.
 *
 * ## Inputs
 * - Environment variables:
 * - `DEBTOR_SERVICE_PROVIDER_ID` (required): Debtor Service Provider identifier used in payloads.
 * - `VU_COUNT_SET` (number, optional, default: 10): number of virtual users.
 * - `ITERATIONS` (number, optional, default: 30000): total iterations across all VUs.
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
export let options = {
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
    stage: determineStage(elapsedSeconds)
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
 * Ensures `testCompletedRef` is set to true before delegating to the shared summary factory,
 * which generates aggregated artifacts and annotates results.
 */
export const handleSummary = (opts) => {
    testCompletedRef.value = true;
    return createHandleSummary({
        START_TIME,
        testName: 'ACTIVATION STRESS TEST',
        countTag: 'requestCount',
        reportPrefix: 'activation',
        VU_COUNT,
        testCompletedRef
    })(opts);
};
