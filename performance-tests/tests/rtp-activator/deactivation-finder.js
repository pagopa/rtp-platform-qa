import http from 'k6/http';
import {check, sleep} from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials} from '../../utils/utils.js';
import {createStandardMetrics} from '../../utils/metrics-utils.js';
import {shuffleArray, distributeItemsAmongGroups} from '../../utils/batch-utils.js';
import {createHandleSummary} from '../../utils/summary-utils.js';
import {createDeactivationTeardown} from '../../utils/teardown-utils.js';

/**
 * @file Multi-VU Deactivation Stress Test (k6)
 * @description
 * Deactivates a set of pre-created activations (read from JSON) using multiple virtual users.
 * Each VU receives a chunk of activation IDs and issues DELETE calls to the deactivation endpoint.
 * Metrics and tags are recorded per-iteration; the run keeps the dashboard open when work is finished.
 *
 * ## Inputs
 * - JSON input: `../../json-file/rtp-activator/activations.json` (array of objects containing an `id` or equivalent field)
 * - Environment variables:
 * - `VU_COUNT_SET` (number, optional, default: 7): number of VUs.
 * - `SLEEP_ITER` (number, seconds, optional, default: 0): sleep after each iteration.
 *
 * ## Outputs
 * - `handleSummary` produces aggregated results and writes standard report files (via `createHandleSummary`).
 */

/** Test start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users to run (from env or default). */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 7;

/** Optional sleep between iterations (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/**
 * Load activations from JSON and normalize to an array of activation IDs.
 * The JSON entries may expose the identifier under different keys (`id`, `activationId`, `activationID`).
 *
 * @type {Array<{ id: string }>} Raw activations file mapped to an array of IDs.
 */
const activations = JSON.parse(open('../../json-file/rtp-activator/activations.json'));
const activationIds = activations
    .map(r => r?.id ?? r?.activationId ?? r?.activationID)
    .filter(id => id != null && id !== '')

/**
 * Working set used by the test, one entry per activation ID, with a deactivation flag.
 * @type {Array<{ id: string, deactivated: boolean }>} wrappedActivations
 */
const wrappedActivations = activationIds.map(id => ({id, deactivated: false}));

/**
 * Standard custom metrics used by this test.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate} currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend} responseTimeTrend
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 options with a shared-iterations scenario: the total number of iterations
 * equals the total number of wrapped activations, distributed across `VU_COUNT_SET` VUs.
 *
 * @type {import('k6/options').Options}
 */
export let options = {
  ...getOptions('stress_test_fixed_user', 'deactivate'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: wrappedActivations.length,
      maxDuration: '30m',
      gracefulStop: '30m',
      exec: 'deactivate'
    }
  }
};

/**
 * Flag toggled when all activations have been deactivated.
 * When `true`, VUs will idle to keep the dashboard available.
 * @type {boolean}
 */
let testCompleted = false;

/**
 * @typedef {Object} SetupData
 * @property {string} access_token Access token for authenticated requests.
 * @property {Array<Array<{ id: string, deactivated: boolean }>>} activationChunks Per-VU activation chunks.
 * @property {number} totalActivations Total number of activations overall.
 * @property {number} deactivatedCount Global count of deactivated activations.
 * @property {boolean} allCompleted Whether the entire test has completed.
 * @property {Object<string, number>=} currentIndices Optional per-VU current index map.
 * @property {Object<string, number>=} vuDeactivatedCount Optional per-VU deactivation counters.
 */


/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER`, shuffles the activation list, and splits it into
 * equal(ish) chunks for the available VUs. Returns the token and chunking metadata as setup data.
 *
 * @returns {SetupData} Data used by the `deactivate` function for work distribution and progress tracking.
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);

  shuffleArray(wrappedActivations);

  const activationChunks = distributeItemsAmongGroups(wrappedActivations, VU_COUNT_SET);

  console.log(`Activations distributed among ${VU_COUNT_SET} virtual users:`);
  for (let i = 0; i < VU_COUNT_SET; i++) {
    console.log(`- VU #${i + 1}: ${activationChunks[i].length} activations`);
  }

  return {
    access_token: auth.access_token,
    activationChunks: activationChunks,
    totalActivations: wrappedActivations.length,
    deactivatedCount: 0,
    allCompleted: false
  };
}

/**
 * Deactivation worker executed by each VU.
 *
 * For the calling VU, picks the current activation from its chunk, performs a DELETE against
 * the deactivation endpoint, records metrics, and advances the index. When all work is complete,
 * sets a global flag to keep the dashboard visible while idling.
 *
 * @param {SetupData} data Setup data produced by `setup()`.
 * @returns {Object} The HTTP response object from k6 or a small status object when idling.
 */
export function deactivate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    deactivatedCount: data.deactivatedCount,
    vu: __VU
  };

  currentRPS.add(1, tags);

  if (testCompleted) {
    console.log(`⏹️ Test already completed. VU #${__VU} staying idle to keep dashboard active...`);
    sleep(30);
    return {
      status: 200,
      message: 'Test already completed, waiting for dashboard viewing',
      noMetrics: true
    };
  }

  const vuIndex = __VU - 1;

  if (!data.activationChunks[vuIndex]) {
    console.log(`⚠️ VU #${__VU}: No activation chunk assigned. Termination.`);
    return { status: 400, message: 'No activation chunk assigned', noMetrics: true };
  }

  const myActivations = data.activationChunks[vuIndex];

  if (data.currentIndices === undefined) {
    data.currentIndices = {};
  }
  if (data.currentIndices[vuIndex] === undefined) {
    data.currentIndices[vuIndex] = 0;
  }

  if (data.vuDeactivatedCount === undefined) {
    data.vuDeactivatedCount = {};
  }
  if (data.vuDeactivatedCount[vuIndex] === undefined) {
    data.vuDeactivatedCount[vuIndex] = 0;
  }

  if (data.vuDeactivatedCount[vuIndex] >= myActivations.length) {
    console.log(`✓ VU #${__VU}: Completed all ${myActivations.length} deactivations assigned.`);
    sleep(5);
    return {
      status: 200,
      message: `VU #${__VU} completed all deactivations, idle for dashboard`,
      noMetrics: true
    };
  }

  const currentIndex = data.currentIndices[vuIndex];
  const activationItem = myActivations[currentIndex];

  if (activationItem.deactivated) {
    data.currentIndices[vuIndex] = (currentIndex + 1) % myActivations.length;
    return deactivate(data);
  }

  const headers = buildHeaders(data.access_token);
  const url = `${endpoints.deactivations}/${activationItem.id}`;

  const start = Date.now();
  const res = http.del(url, null, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 204) {
    successCounter.add(1, tags);

    activationItem.deactivated = true;
    data.vuDeactivatedCount[vuIndex]++;
    data.deactivatedCount++;

    if (data.deactivatedCount % 50 === 0 || data.vuDeactivatedCount[vuIndex] === data.activationChunks[vuIndex].length) {
      console.log(`✓ VU #${__VU}: ${data.vuDeactivatedCount[vuIndex]}/${data.activationChunks[vuIndex].length} deactivations completed (Total: ${data.deactivatedCount}/${data.totalActivations})`);
    }

    if (data.deactivatedCount >= data.totalActivations && !data.allCompleted) {
      data.allCompleted = true;
      testCompleted = true;
      console.log(`✅ TEST COMPLETED: All ${data.totalActivations} activations have been deactivated!`);
      console.log(`Total execution time: ${Math.round(elapsedSeconds)} seconds`);
      console.log(`Dashboard will remain active for viewing results.`);
      return {
        status: 204,
        message: 'Test completed successfully, dashboard still active',
        noMetrics: false
      };
    }
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Failed deactivation for ID ${activationItem.id}: Status ${res.status}`);
  }

  check(res, {
    'deactivation: status is 204': (r) => r.status === 204
  });

  data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % myActivations.length;

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

  return res;
}

/**
 * Small helper that exposes `testCompleted` as a mutable reference for teardown utilities.
 * The property descriptor ensures reads/writes affect the module-scoped variable above.
 */
const testCompletedRef = { value: false };
Object.defineProperty(testCompletedRef, 'value', {
  get: () => testCompleted,
  set: (v) => { testCompleted = v; }
});

/**
 * k6 `teardown` export created via a specialized utility for deactivation tests.
 *
 * It forwards deactivation-specific fields to the generic batch-processing teardown
 * and logs a concise end-of-test summary.
 */
export const teardown = createDeactivationTeardown({
  START_TIME,
  VU_COUNT: VU_COUNT_SET,
  testCompletedRef
});

/**
 * k6 `handleSummary` export created by a summary factory.
 *
 * Produces HTML/JSON summaries with a consistent naming scheme and derives completion
 * state from global variables or metrics when available.
 */
export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'MULTI-VU DEACTIVATION STRESS TEST',
  countTag: 'deactivatedCount',
  reportPrefix: 'deactivation',
  VU_COUNT: VU_COUNT_SET
});
