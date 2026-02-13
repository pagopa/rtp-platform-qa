import http from 'k6/http';
import {check, sleep} from 'k6';
import {createStandardMetrics} from "../../utils/metrics-utils.js";
import {
  ActorCredentials,
  buildHeaders,
  determineStage,
  endpoints,
  generatePositiveLong,
  getOptions,
  setupAuth
} from "../../utils/utils.js";
import {buildGpdMessagePayload} from "../../utils/sender-payloads.js";
import {uuidv4} from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users. */
const VU_COUNT = Number(__ENV.VU_COUNT_SET) || 10;

/** Total shared iterations. */
const ITERATIONS = Number(__ENV.ITERATIONS) || 1000;

/** Optional sleep between iterations (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** Creditor entity tax code. */
const EC_TAX_CODE = String(__ENV.EC_TAX_CODE);

/** Optional PSP tax code. If not provided, the value defaults to null. */
const PSP_TAX_CODE = String(__ENVPSP_TAX_CODE) || null;

/**
 * Per-VU authentication token management.
 * Each VU keeps its own token instance and refresh timestamp.
 */
let consumerToken = null;
let tokenCreatedAt = 0;

/**
 * Token time-to-live in milliseconds (15 minutes).
 */
const TOKEN_TTL = 15 * 60 * 1000;

/**
 * Loads activation fiscal codes from external JSON file.
 *
 * Steps:
 *  - Reads the activations.json file
 *  - Extracts fiscalCode values
 *  - Filters out null/empty entries
 *  - Removes duplicates using Set
 *  - Normalizes all values to String
 *
 * Result: unique list of valid fiscal codes used during the test.
 */
const activationFiscalCodes = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activations.json'))
    .map(r => r?.fiscalCode)
    .filter(fc => fc != null && fc !== '')
)).map(String);

/**
 * Standard custom metrics used by this test.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate} currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend} responseTimeTrend
 */
const {
  currentRPS,
  failureCounter,
  successCounter,
  responseTimeTrend
} = createStandardMetrics();

/**
 * Returns a random element from the given array.
 *
 * @param {Array<any>} arr - Source array
 * @returns {any} Random element
 */
function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * k6 execution configuration.
 * Uses shared-iterations executor with configurable VUs and iterations.
 */
export const options = {
  ...getOptions('stress_test_fixed_user', 'sendMessage'),
  setupTimeout: '2m',
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT,
      iterations: ITERATIONS,
      maxDuration: '240m',
      gracefulStop: '30s',
      exec: 'sendMessage'
    }
  }
};

/**
 * k6 setup function.
 *
 * Executed once before the test starts.
 * Prepares and wraps fiscal codes to be shared across VUs.
 *
 * @returns {{ fiscalCodes: Array<{fiscalCode: string}> }}
 */
export function setup() {
  const wrappedActivations = activationFiscalCodes.map(
      fiscalCode => ({fiscalCode}));
  return {fiscalCodes: wrappedActivations};
}

/**
 * Main stress test scenario function.
 *
 * For each iteration:
 *  - Calculates time-based tags for metrics
 *  - Refreshes the authentication token every TOKEN_TTL
 *  - Sends a GPD message request
 *  - Tracks success/failure and response time
 *
 * @param {{ fiscalCodes: Array<{fiscalCode: string}> }} data - Shared setup data
 */
export function sendMessage(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU),
  };

  currentRPS.add(1, tags);

  if (!consumerToken || (Date.now() - tokenCreatedAt) > TOKEN_TTL) {
    const auth = setupAuth(ActorCredentials.RTP_CONSUMER);
    consumerToken = auth.access_token;
    tokenCreatedAt = Date.now();
    console.log(`🔄 VU ${__VU} refreshed token`);
  }


  const headers = {
    ...buildHeaders(consumerToken),
    "Idempotency-Key": uuidv4()
  };

  const picked = randomItem(data.fiscalCodes);
  const fiscalCode = picked?.fiscalCode;

  const payload = buildGpdMessagePayload(
      fiscalCode,
      generatePositiveLong(),
      "CREATE",
      "VALID",
      EC_TAX_CODE,
      PSP_TAX_CODE
  );

  const start = Date.now();
  let res = http.post(endpoints.gpdMessage, JSON.stringify(payload), {headers});
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 200) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(
        `❌ VU #${__VU}: Failed send gpd message — Status ${res.status}`);
  }

  check(res, {
    'GpdMessage: status is 200': (r) => r.status === 200
  });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }
}
