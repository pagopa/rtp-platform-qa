import http from 'k6/http';
import {check, sleep} from 'k6';
import {createStandardMetrics} from "../../utils/metrics-utils.js";
import {
  ActorCredentials,
  buildHeaders,
  determineStage,
  endpoints,
  getOptions,
  setupAuth
} from "../../utils/utils.js";

/**
 * @file RTP Takeover - k6 Stress Test Script
 *
 * @description
 * Executes takeover operations for previously generated RTP activation OTPs.
 * OTPs are loaded from a JSON file and distributed across Virtual Users using
 * the `shared-iterations` executor.
 *
 * This script authenticates once during the k6 `setup()` phase and passes the
 * access token to all VUs via `setup_data` (the `data` parameter in `takeover()`),
 * avoiding token refresh during execution.
 *
 * Each iteration processes exactly one OTP, ensuring no duplication during a run.
 *
 * ## Environment Variables
 * - `VU_COUNT_SET` (optional, default: 10): Number of Virtual Users.
 * - `SLEEP_ITER` (optional, seconds, default: 0): Sleep time between iterations.
 *
 * ## Input
 * - File: `json-file/rtp-activator/activation-otps.json`
 * - Format: JSON array of OTP strings
 *
 * ## Execution Strategy
 * - Executor: `shared-iterations`
 * - Iterations: equals the number of OTPs loaded from file
 * - OTP mapping: `activationOtps[__ITER]` (1 OTP per iteration)
 */

/** Timestamp (ms) marking the start of the test run. */
const START_TIME = Date.now();

/** Number of Virtual Users (configurable via environment variable). */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Optional per-iteration sleep time (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/**
 * Loads activation OTPs from file.
 * Duplicate entries are removed using a Set.
 *
 * @type {string[]}
 */
const activationOtps = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activation-otps.json'))
)).map(String);

/**
 * Custom performance metrics.
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 execution options.
 *
 * Uses shared iterations so each OTP is processed exactly once.
 *
 * @type {import('k6/options').Options}
 */
export const options = {
  ...getOptions('stress_test_fixed_user', 'takeover'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: activationOtps.length,
      maxDuration: '30m',
      gracefulStop: '30m',
      exec: 'takeover'
    }
  }
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates once as `DEBTOR_SERVICE_PROVIDER` and returns the access token.
 * The returned object is available to the scenario function as the `data` parameter.
 *
 * @returns {{ token: string }} Object containing the access token used for takeover requests.
 */
export function setup(){

  const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
  return {token : auth.access_token};
}

/**
 * k6 scenario function.
 *
 * Performs a takeover operation for one activation OTP.
 *
 * Flow per iteration:
 * - Derives tags for metrics (timeWindow, stage, vu)
 * - Picks an OTP using the global iteration index (`__ITER`)
 * - Calls takeover endpoint with the token provided by `setup()`
 * - Records response time and success/failure metrics
 * - Optionally sleeps between iterations
 *
 * @param {{ token: string }} data Data returned by `setup()` (available as `setup_data`).
 * @returns {void}
 */
export function takeover(data){

  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU),
  };

  currentRPS.add(1, tags);

  const token = data.token;

  const otp = activationOtps[__ITER];

  const endpoint = `${endpoints.takeover}/${otp}`
  const headers = { ...buildHeaders(token)};

  const start = Date.now();
  let res = http.post(endpoint, null, {headers});
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 201) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(
        `❌ VU #${__VU}: Failed takeover — Status ${res.status}`);
  }

  check(res, {
    'Takeover: status is 201': (r) => r.status === 201
  });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

}
