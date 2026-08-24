import http from 'k6/http';
import { check, sleep } from 'k6';
import {
  ActorCredentials,
  buildHeaders,
  determineStage,
  endpoints,
  getOptions,
  setupAuth,
} from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { shuffleArray, distributeItemsAmongGroups } from '../../utils/batch-utils.js';

/**
 * @file Delivery-Status Finder – Stress Test (k6)
 * @description
 * Executes high-throughput GET requests to the `GET /rtps/delivery-status` endpoint.
 *
 * Each VU picks a pair of `{ noticeNumber, payeeId }` from its pre-assigned slice of
 * the fixture file and fires one GET request per iteration.
 *
 * ## Prerequisites
 * Run `script/create-delivery-status.js` first to generate the fixture file:
 *   k6 run script/create-delivery-status.js
 *
 * ## Inputs — Environment variables
 * | Variable        | Default | Description                                     |
 * |-----------------|---------|--------------------------------------------------|
 * | `VU_COUNT_SET`  | 10      | Number of virtual users                          |
 * | `ITERATIONS`    | 1000    | Total shared iterations across all VUs           |
 * | `SLEEP_ITER`    | 0       | Optional sleep (seconds) between iterations       |
 *
 * ## Input file
 * `../../json-file/rtp-sender/delivery-status-inputs.json`
 * Array of `{ noticeNumber: string, payeeId: string }` produced by the data script.
 *
 * ## Metrics collected
 * Standard metrics via `createStandardMetrics()`:
 *  - `currentRPS`        – request rate counter
 *  - `successCounter`    – HTTP 200 count
 *  - `failureCounter`    – non-200 count
 *  - `responseTimeTrend` – response time distribution
 */

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users (env: VU_COUNT_SET, default: 10). @type {number} */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Total shared iterations (env: ITERATIONS, default: 1000). @type {number} */
const ITERATIONS = Number(__ENV.ITERATIONS) || 1000;

/** Optional sleep between iterations in seconds (env: SLEEP_ITER, default: 0). @type {number} */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/**
 * Delivery-status inputs loaded from the fixture file produced by
 * `script/create-delivery-status.js`.
 *
 * @type {Array<{ noticeNumber: string, payeeId: string }>}
 */
const deliveryStatusInputs = JSON.parse(
  open('../../json-file/rtp-sender/delivery-status-inputs.json')
);

if (!deliveryStatusInputs || deliveryStatusInputs.length === 0) {
  throw new Error(
    '❌ delivery-status-inputs.json is empty or missing inputs.\n' +
    'Generate the fixture first by running:\n' +
    '  ./run-tests.sh script/create-delivery-status.js console\n' +
    'Make sure DEBTOR_FISCAL_CODE and EC_TAX_CODE are set in ../.env'
  );
}

/**
 * Standard custom metrics.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate}   currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend}  responseTimeTrend
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } =
  createStandardMetrics();

/**
 * Mutable reference observed by teardown / summary utilities.
 * @type {{ value: boolean }}
 */
const testCompletedRef = { value: false };

/**
 * k6 scenario options.
 *
 * @type {import('k6/options').Options}
 */
export const options = {
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
 * @typedef {Object} SetupData
 * @property {string} accessToken - Bearer access token.
 * @property {Array<Array<{ noticeNumber: string, payeeId: string }>>} inputChunks
 *   Delivery-status inputs distributed by VU index.
 */

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER`, shuffles the inputs for randomness, and
 * distributes them among VUs so that each VU owns a deterministic, non-overlapping slice.
 *
 * @returns {SetupData} Shared data passed to every VU iteration.
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
  const accessToken = auth.access_token;

  if (!deliveryStatusInputs || deliveryStatusInputs.length === 0) {
    throw new Error(
      '❌ delivery-status-inputs.json is empty or missing. ' +
        'Run `k6 run script/create-delivery-status.js` first.'
    );
  }

  const shuffled = deliveryStatusInputs.slice();
  shuffleArray(shuffled);

  const inputChunks = distributeItemsAmongGroups(shuffled, VU_COUNT_SET);

  console.log(`✅ Setup complete — ${shuffled.length} inputs distributed across ${VU_COUNT_SET} VUs`);
  for (let i = 0; i < VU_COUNT_SET; i++) {
    console.log(`  - VU #${i + 1}: ${inputChunks[i].length} items`);
  }

  return { accessToken, inputChunks };
}

/**
 * Per-VU iteration index. Tracks how many requests each VU has issued so far,
 * enabling sequential consumption of its assigned inputs slice.
 *
 * @type {Record<number, number>}
 */
const vuIterIndex = {};

/**
 * Main stress-test scenario function.
 *
 * For each iteration:
 *  1. Picks the next `{ noticeNumber, payeeId }` pair from the VU's assigned chunk,
 *     cycling back to the beginning when the slice is exhausted.
 *  2. Sends `GET /rtps/delivery-status?noticeNumber=<nav>&payeeId=<ec_tax_code>`.
 *  3. Records success / failure and response-time metrics.
 *
 * Both `PD_RTP_DELIVERED` and `PD_RTP_NOT_DELIVERED` responses are treated as
 * successful (HTTP 200), as the endpoint always returns 200 for valid inputs.
 *
 * @param {SetupData} data - Shared data returned by `setup()`.
 */
export function checkDeliveryStatus(data) {
  const vu = __VU;
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(vu),
  };

  currentRPS.add(1, tags);

  // Resolve the input pair for this VU / iteration
  const vuIndex = vu - 1;
  const myChunk = data.inputChunks[vuIndex] || [];

  if (myChunk.length === 0) {
    console.warn(`⚠️ VU #${vu}: No inputs assigned — skipping iteration.`);
    failureCounter.add(1, tags);
    return;
  }

  if (vuIterIndex[vu] === undefined) {
    vuIterIndex[vu] = 0;
  }

  const input = myChunk[vuIterIndex[vu] % myChunk.length];
  vuIterIndex[vu]++;

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

    // Log the delivery status value for observability (sampled every 100 iterations)
    if (vuIterIndex[vu] % 100 === 0) {
      try {
        const body = res.json();
        console.log(`VU #${vu} [iter ${vuIterIndex[vu]}]: status=${body.status}, processingDate=${body.processingDate}`);
      } catch (_) {
        // ignore JSON parse errors in logging
      }
    }
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
export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'GetDeliveryStatus STRESS TEST',
  countTag: 'requestCount',
  reportPrefix: 'deliveryStatus',
  VU_COUNT: VU_COUNT_SET,
  testCompletedRef,
});
