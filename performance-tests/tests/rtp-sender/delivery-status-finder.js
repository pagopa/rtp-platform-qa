import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import {
  ActorCredentials,
  buildHeaders,
  getStageLabel,
  endpoints,
  getOptions,
  setupAuth,
  describeScenarioVUs,
} from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';

/**
 * @file Delivery-Status Finder – Stress Test (k6)
 * @description
 * Executes high-throughput GET requests to the `GET /rtps/delivery-status` endpoint.
 *
 * Each iteration dynamically picks a pair of `{ noticeNumber, payeeId }` from the
 * fixture file using the test iteration index (cycling if iterations > inputs count).
 *
 * ## Prerequisites
 * Run `script/create-delivery-status.js` first to generate the fixture file:
 *   k6 run script/create-delivery-status.js
 *
 * ## Inputs — Environment variables
 * | Variable        | Default | Description                                     |
 * |-----------------|---------|--------------------------------------------------|
 * | `SCENARIO`       | custom  | Load profile (custom, stress_test, soak_test, spike_test) |
 * | `VU_COUNT_SET`  | 10      | Number of virtual users                          |
 * | `ITERATIONS`    | inputs  | Total shared iterations across all VUs           |
 * | `SLEEP_ITER`    | 0       | Optional sleep (seconds) between iterations       |
 *
 * ## Input file
 * `../../json-file/rtp-sender/delivery-status-inputs.json`
 * Array of `{ noticeNumber: string, payeeId: string }` produced by the data script.
 */

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users (env: VU_COUNT_SET, default: 10). @type {number} */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Optional sleep between iterations in seconds (env: SLEEP_ITER, default: 0). @type {number} */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

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

/**
 * Delivery-status inputs loaded from the fixture file produced by
 * `script/create-delivery-status.js`.
 *
 * @type {Array<{ noticeNumber: string, payeeId: string }>}
 */
let rawInputs;
try {
  rawInputs = open('../../json-file/rtp-sender/delivery-status-inputs.json');
} catch (e) {
  rawInputs = '[]';
}

const deliveryStatusInputs = JSON.parse(rawInputs);

if (!deliveryStatusInputs || deliveryStatusInputs.length === 0) {
  throw new Error(
    '❌ delivery-status-inputs.json is empty or missing inputs.\n' +
    'Generate the fixture first by running:\n' +
    '  ./run-tests.sh script/create-delivery-status.js console'
  );
}

/** Total shared iterations (env: ITERATIONS, default: deliveryStatusInputs count). @type {number} */
const ITERATIONS = Number(__ENV.ITERATIONS) || deliveryStatusInputs.length;

/** Standard performance metrics. */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/** Mutable reference observed by teardown / summary utilities. @type {{ value: boolean }} */
const testCompletedRef = { value: false };

/**
 * k6 scenario options.
 *
 * @type {import('k6/options').Options}
 */
export const options = PREDEFINED_SCENARIOS.includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, 'checkDeliveryStatus'),
      setupTimeout: '5m',
    }
  : {
      ...getOptions('stress_test_fixed_user', 'checkDeliveryStatus'),
      setupTimeout: '5m',
      scenarios: {
        stress_test_fixed_user: {
          executor: 'shared-iterations',
          vus: VU_COUNT_SET,
          iterations: ITERATIONS,
          maxDuration: '240m',
          gracefulStop: '30s',
          exec: 'checkDeliveryStatus',
        },
      },
    };

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER`.
 *
 * @returns {{ accessToken: string }} Shared data passed to every VU iteration.
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
  return { accessToken: auth.access_token };
}

/**
 * Main stress-test scenario function.
 *
 * For each iteration:
 *  1. Picks the next `{ noticeNumber, payeeId }` pair from `deliveryStatusInputs`
 *     using the scenario iteration index (cycling across the list).
 *  2. Sends `GET /rtps/delivery-status?noticeNumber=<nav>&payeeId=<ec_tax_code>`.
 *  3. Records success / failure and response-time metrics.
 *
 * @param {{ accessToken: string }} data - Shared data returned by `setup()`.
 */
export function checkDeliveryStatus(data) {
  const vu = __VU;
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const iteration = exec.scenario.iterationInTest;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: getStageLabel(SCENARIO, elapsedSeconds),
    vu: String(vu),
  };

  currentRPS.add(1, tags);

  // Pick input by global scenario iteration, cycling safely across available inputs
  const input = deliveryStatusInputs[iteration % deliveryStatusInputs.length];

  const headers = buildHeaders(data.accessToken);
  const url =
    `${endpoints.deliveryStatus}` +
    `?noticeNumber=${encodeURIComponent(input.noticeNumber)}` +
    `&payeeId=${encodeURIComponent(input.payeeId)}`;

  const start = Date.now();
  const res = http.get(url, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  check(res, {
    'DeliveryStatus: status is 200': (r) => r.status === 200,
  });

  if (res.status === 200) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(
      `❌ VU #${vu}: GET delivery-status failed — HTTP ${res.status} ` +
        `(noticeNumber=${input.noticeNumber}, payeeId=${input.payeeId})`
    );
  }

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }
}

/**
 * k6 `handleSummary` export created by the summary factory.
 */
export const handleSummary = (opts) => {
  return createHandleSummary({
    START_TIME,
    testName: 'GetDeliveryStatus STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'deliveryStatus',
    VU_COUNT: describeScenarioVUs(SCENARIO, VU_COUNT_SET),
    testCompletedRef,
    scenarioConfig: options.scenarios ? options.scenarios[SCENARIO] : undefined,
  })(opts);
};
