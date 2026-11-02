/**
 * @file Payees Endpoint Stress Test (k6)
 * @description
 * High-throughput performance and load testing for the Payees registry endpoint:
 *   GET /payees/payees?page=${page}&size=${size}
 *
 * ## Inputs — Environment Variables
 * | Variable                                    | Default | Description                                                     |
 * |---------------------------------------------|---------|-----------------------------------------------------------------|
 * | `SCENARIO`                                  | custom  | Load profile (custom, stress_test, soak_test, spike_test)        |
 * | `VU_COUNT_SET`                              | 10      | Number of virtual users                                          |
 * | `ITERATIONS`                                | 1000    | Total shared iterations across all VUs (custom scenario)        |
 * | `SLEEP_ITER`                                | 0       | Sleep time (seconds) between iterations                         |
 * | `PAGE`                                      | 0       | Pagination page number                                          |
 * | `SIZE`                                      | 20      | Pagination page size                                            |
 * | `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_ID`     | -   | Client ID for OAuth token retrieval (required)                  |
 * | `PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_SECRET` | -   | Client secret for OAuth token retrieval (required)              |
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import {
  setupAuth,
  buildHeaders,
  getStageLabel,
  getOptions,
  describeScenarioVUs,
  ActorCredentials,
  endpoints
} from '../../utils/utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users (env: VU_COUNT_SET, default: 10). */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Total shared iterations (env: ITERATIONS, default: 1000). */
const ITERATIONS = Number(__ENV.ITERATIONS) || 1000;

/** Optional per-iteration sleep in seconds (env: SLEEP_ITER, default: 0). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** Pagination query parameters. */
const PAGE = __ENV.PAGE || 0;
const SIZE = __ENV.SIZE || 20;

/** Load profile to use. */
const SCENARIO = __ENV.SCENARIO || 'custom';

/** Scenario names backed by progressiveOptions in utils.js */
const PREDEFINED_SCENARIOS = [
  'stress_test', 'soak_test', 'spike_test',
  'stress_test_fixed_user', 'soak_test_fixed_user', 'spike_test_fixed_user'
];

if (SCENARIO !== 'custom' && !PREDEFINED_SCENARIOS.includes(SCENARIO)) {
  throw new Error(
    `❌ Unknown SCENARIO "${SCENARIO}". Expected one of: 'custom', ${PREDEFINED_SCENARIOS.map((s) => `'${s}'`).join(', ')}`
  );
}

/** Standard performance metrics */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/** Mutable ref object for test completion state. */
const testCompletedRef = { value: false };

/**
 * k6 execution options.
 * @type {import('k6/options').Options}
 */
export let options = PREDEFINED_SCENARIOS.includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, 'testGetPayees'),
      setupTimeout: '5m'
    }
  : {
      ...getOptions('stress_test_fixed_user', 'testGetPayees'),
      setupTimeout: '5m',
      scenarios: {
        stress_test_fixed_user: {
          executor: 'shared-iterations',
          vus: VU_COUNT_SET,
          iterations: ITERATIONS,
          maxDuration: '240m',
          gracefulStop: '30s',
          exec: 'testGetPayees'
        }
      }
    };

/**
 * Performs authentication setup using PAGOPA_INTEGRATION_PAYEE_REGISTRY credentials.
 *
 * @returns {Object} Shared data object containing the access token
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.PAGOPA_INTEGRATION_PAYEE_REGISTRY);
  return {
    accessToken: auth.access_token,
    startTime: Date.now(),
    totalIterations: ITERATIONS
  };
}

/**
 * Executes the main test logic:
 * - tracks metrics (RPS, response time)
 * - builds headers with auth, versioning, request ID
 * - sends GET request to /payees/payees with pagination
 * - checks status 200, increments success/failure counters
 *
 * @param {{ accessToken: string }} data - Setup data containing the access token
 * @returns {Response} The HTTP response object
 */
export function testGetPayees(data) {
  const vu = __VU;
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const iteration = exec.scenario.iterationInTest;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: getStageLabel(SCENARIO, elapsedSeconds),
    requestCount: String(iteration + 1),
    vu: String(vu)
  };

  currentRPS.add(1, tags);

  const headers = buildHeaders(data.accessToken || data.access_token);
  headers['RequestId'] = uuidv4();
  headers['Version'] = 'v1';

  const url = `${endpoints.payees}?page=${PAGE}&size=${SIZE}`;

  const start = Date.now();
  const res = http.get(url, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  const isOk = res.status === 200;
  check(res, {
    'payees: status is 200': () => isOk
  });

  if (isOk) {
    successCounter.add(1, tags);
    if (iteration + 1 >= ITERATIONS) {
      testCompletedRef.value = true;
    }
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${vu}: GET payees failed — HTTP ${res.status}`);
  }

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

  return res;
}

/**
 * Summary report generator for this test run.
 */
export const handleSummary = (data) => {
  const scenario = options.scenarios?.[SCENARIO];
  if (SCENARIO === 'custom' || (scenario?.executor === 'constant-vus' && data.state)) {
    const completed = SCENARIO === 'custom'
      ? (data.metrics?.iterations?.values?.count ?? 0) >= ITERATIONS
      : !data.state.isInterrupted;
    testCompletedRef.value = completed;
    data.setup_data = { ...data.setup_data, testCompleted: completed };
  }

  return createHandleSummary({
    START_TIME,
    testName: 'PAYEES ENDPOINT STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'payees',
    VU_COUNT: describeScenarioVUs(SCENARIO, VU_COUNT_SET),
    testCompletedRef,
    scenarioConfig: options.scenarios ? options.scenarios[SCENARIO] : undefined
  })(data);
};
