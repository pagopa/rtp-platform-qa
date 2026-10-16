import http from 'k6/http';
import {check, sleep} from 'k6';
import exec from 'k6/execution';
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
 * the configured scenario executor.
 *
 * This script authenticates once during the k6 `setup()` phase and passes the
 * access token to all VUs via `setup_data` (the `data` parameter in `takeover()`),
 * avoiding token refresh during execution.
 *
 * Each iteration processes an OTP using the scenario iteration index (`exec.scenario.iterationInTest`),
 * ensuring no duplication across concurrent VUs during a run.
 *
 * ## Environment Variables
 * - `SCENARIO` (optional, default: 'stress_test_fixed_user'): Load profile to execute.
 *   Supports 'stress_test', 'soak_test', 'spike_test', or 'stress_test_fixed_user' / 'custom'.
 * - `VU_COUNT_SET` (optional, default: 10): Number of Virtual Users.
 * - `ITERATIONS` (optional, default: OTP count): Total iterations (used when SCENARIO is custom/fixed).
 * - `SLEEP_ITER` (optional, seconds, default: 0): Sleep time between iterations.
 *
 * ## Input
 * - File: `json-file/rtp-activator/activation-otps.json`
 * - Format: JSON array of OTP strings
 *
 * ## Execution Strategy
 * - OTP mapping: `activationOtps[exec.scenario.iterationInTest]` (1 OTP per iteration)
 */

/** Timestamp (ms) marking the start of the test run. */
const START_TIME = Date.now();

/** Number of Virtual Users (configurable via environment variable). */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Optional per-iteration sleep time (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** Load profile to use. Defaults to 'custom' if not specified. */
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
 * Loads activation OTPs from file.
 * Duplicate entries are removed using a Set.
 *
 * @type {string[]}
 */
const activationOtps = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activation-otps.json'))
)).map(String);

/** Total shared iterations for the scenario. */
const ITERATIONS = Number(__ENV.ITERATIONS) || activationOtps.length;

/**
 * Custom performance metrics.
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 execution options.
 *
 * Configures the scenario dynamically based on SCENARIO:
 * - Predefined arrival-rate scenarios (stress_test, soak_test, spike_test) use getOptions().
 * - 'custom' or 'stress_test_fixed_user' use a shared-iterations executor across the loaded OTPs.
 *
 * @type {import('k6/options').Options}
 */
export const options = PREDEFINED_SCENARIOS.includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, 'takeover'),
      setupTimeout: '5m'
    }
  : {
      ...getOptions('stress_test_fixed_user', 'takeover'),
      setupTimeout: '5m',
      scenarios: {
        stress_test_fixed_user: {
          executor: 'shared-iterations',
          vus: VU_COUNT_SET,
          iterations: Math.min(ITERATIONS, activationOtps.length),
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
 * - Picks an OTP using the scenario iteration index (`exec.scenario.iterationInTest`)
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

  const otpIndex = exec.scenario.iterationInTest;
  if (otpIndex >= activationOtps.length) {
    exec.test.abort(`OTPs exhausted (${activationOtps.length})`);
    return;
  }

  const token = data.token;
  const otp = activationOtps[otpIndex];

  const endpoint = `${endpoints.takeover}/${otp}`;
  const headers = { ...buildHeaders(token)};

  currentRPS.add(1, tags);

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
