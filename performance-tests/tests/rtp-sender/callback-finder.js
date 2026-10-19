import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { endpoints, determineStage, getOptions } from "../../utils/utils.js";
import { HOST_SUFFIX } from "../../config/config.js";
import { createStandardMetrics } from "../../utils/metrics-utils.js";
import { createHandleSummary } from "../../utils/summary-utils.js";
import { buildCallbackPayload } from "../../utils/sender-payloads.js";
import { createCallbackTeardown } from "../../utils/teardown-utils.js";

/**
 * @file RTP Callback - k6 Test Script
 *
 * @description
 * Executes callback send operations for previously generated RTP resource IDs.
 * Resource IDs are loaded from JSON and executed using the configured scenario executor.
 *
 * ## Environment Variables
 * - `SCENARIO` (optional, default: 'custom'): Load profile to execute.
 *   Supports 'stress_test', 'soak_test', 'spike_test', or 'stress_test_fixed_user' / 'custom'.
 * - `VU_COUNT_SET` (optional, default: 5): Number of Virtual Users.
 * - `ITERATIONS` (optional, default: resourceIds count): Total iterations across all VUs.
 * - `SLEEP_ITER` (optional, seconds, default: 0): Sleep time between iterations.
 *
 * ## Inputs
 * - File: `json-file/rtp-sender/resourceIds.json` (fallback: `script/resourceIds.json`)
 * - Certificates: `utils/certificates/cert.pem`, `utils/certificates/key-unencrypted.pem`
 */

/** Timestamp (ms) marking the start of the test run. */
const START_TIME = Date.now();

/** Number of Virtual Users (configurable via environment variable). */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 5;

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

/** Paths to mTLS certificates */
const MTLS_CERT_PATH = '../../utils/certificates/cert.pem';
const MTLS_KEY_PATH  = '../../utils/certificates/key-unencrypted.pem';

/**
 * Loads RTP resource IDs from JSON file.
 * Tries `json-file/rtp-sender/resourceIds.json` first, then falls back to `script/resourceIds.json`.
 */
let rawResourceIds;
try {
  rawResourceIds = open('../../json-file/rtp-sender/resourceIds.json');
} catch (e) {
  rawResourceIds = open('../../script/resourceIds.json');
}
const resourceIds = Array.from(new Set(JSON.parse(rawResourceIds))).map(String);

/** Total shared iterations for the scenario. */
const ITERATIONS = Number(__ENV.ITERATIONS) || resourceIds.length;

/** Standard performance metrics used in the test. */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 execution options.
 *
 * Configures the scenario dynamically based on SCENARIO:
 * - Predefined arrival-rate scenarios (stress_test, soak_test, spike_test) use getOptions().
 * - 'custom' or 'stress_test_fixed_user' use a shared-iterations executor across the loaded resource IDs.
 *
 * @type {import('k6/options').Options}
 */
export let options = ['stress_test', 'soak_test', 'spike_test'].includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, 'callback'),
      setupTimeout: '5m',
      tlsAuth: [
        {
          domains: [`api-rtp-cb.${HOST_SUFFIX}`],
          cert: open(MTLS_CERT_PATH),
          key: open(MTLS_KEY_PATH),
        }
      ],
      insecureSkipTLSVerify: true
    }
  : {
      ...getOptions('stress_test_fixed_user', 'callback'),
      setupTimeout: '5m',
      scenarios: {
        stress_test_fixed_user: {
          executor: 'shared-iterations',
          vus: VU_COUNT_SET,
          iterations: Math.min(ITERATIONS, resourceIds.length),
          maxDuration: '30m',
          gracefulStop: '30m',
          exec: 'callback'
        }
      },
      tlsAuth: [
        {
          domains: [`api-rtp-cb.${HOST_SUFFIX}`],
          cert: open(MTLS_CERT_PATH),
          key: open(MTLS_KEY_PATH),
        }
      ],
      insecureSkipTLSVerify: true
    };

/** Indicates whether the test has completed. @type {boolean} */
let testCompleted = false;

/**
 * k6 setup lifecycle function.
 */
export function setup() {
  return {
    totalCallback: resourceIds.length,
    callbackCount: 0,
    allCompleted: false
  };
}

/**
 * Callback execution function per iteration.
 */
export function callback(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU)
  };

  const idx = exec.scenario.iterationInTest;
  if (idx >= resourceIds.length) {
    exec.test.abort(`Resource IDs exhausted (${resourceIds.length})`);
    return;
  }

  const id = resourceIds[idx];
  const payload = JSON.stringify(buildCallbackPayload(id));
  const headers = { 'Content-Type': 'application/json' };
  const url = endpoints.callbackSend;

  currentRPS.add(1, tags);

  const start = Date.now();
  const res = http.post(url, payload, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status >= 200 && res.status < 300) {
    successCounter.add(1, tags);
    if (idx + 1 >= Math.min(ITERATIONS, resourceIds.length)) {
      testCompleted = true;
    }
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Failed callback for ID ${id}: Status ${res.status}`);
  }

  check(res, { 'callback: status is 2xx': (r) => r.status >= 200 && r.status < 300 });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

  return res;
}

const testCompletedRef = { value: false };

export const teardown = createCallbackTeardown({
  START_TIME,
  VU_COUNT: VU_COUNT_SET,
  testCompletedRef
});

Object.defineProperty(testCompletedRef, 'value', {
  get: () => testCompleted,
  set: (newValue) => { testCompleted = newValue; }
});

export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'MULTI-VU CALLBACK STRESS TEST',
  countTag: 'callbackCount',
  reportPrefix: 'callback',
  VU_COUNT: VU_COUNT_SET
});
