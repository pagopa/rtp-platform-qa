import http from 'k6/http';
import {check, sleep} from 'k6';
import {endpoints, determineStage, getOptions} from '../../utils/utils.js';
import {createStandardMetrics} from '../../utils/metrics-utils.js';
import {shuffleArray, distributeItemsAmongGroups} from '../../utils/batch-utils.js';
import {buildCallbackCancelPayload} from "../../utils/sender-payloads.js";

/**
 * @file RTP Callback Cancel Stress Test (k6)
 * @description
 * Executes callback cancel requests for previously generated RTP resource IDs.
 * Resource IDs are distributed among virtual users (VUs) and executed using
 * a fixed shared-iterations scenario.
 *
 * ## Flow
 * 1. Load RTP resource IDs from JSON file.
 * 2. Shuffle IDs to avoid sequential patterns.
 * 3. Distribute IDs evenly among VUs.
 * 4. Each VU performs callback cancel requests for its assigned IDs.
 *
 * ## Metrics
 * - Requests per second (RPS)
 * - Response time trend
 * - Success / failure counters
 *
 * ## Input file
 * `json-file/rtp-sender/resourceIds-cancel.json`
 */

const START_TIME = Date.now();

/** Number of virtual users (`VU_COUNT_SET`, default: 10). @type {number} */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Optional sleep between iterations in seconds (`SLEEP_ITER`). @type {number} */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** RTP Service Provider identifier (`RTP_SP_ID`). @type {string} */
const RTP_SP_ID = String(__ENV.RTP_SP_ID);

/** Path to mTLS certificate used for callback authentication. @type {string} */
const MTLS_CERT_PATH = '../../utils/certificates/cert.pem';

/** Path to mTLS private key used for callback authentication. @type {string} */
const MTLS_KEY_PATH = '../../utils/certificates/key-unencrypted.pem';

/**
 * Unique RTP resource IDs loaded from file.
 * @type {string[]}
 */
const resourceIds = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-sender/resourceIds-cancel.json'))
)).map(String);

/**
 * Standard performance metrics used in the test.
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 test configuration.
 * Defines a shared-iterations scenario where callbacks are distributed
 * across virtual users.
 */
export const options = {
  ...getOptions('stress_test_fixed_user', 'callbackCancel'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: resourceIds.length,
      maxDuration: '30m',
      gracefulStop: '30m',
      exec: 'callbackCancel'
    }
  },
  tlsAuth: [{
    domains: ['api-rtp-cb.dev.cstar.pagopa.it'],
    cert: open(MTLS_CERT_PATH),
    key: open(MTLS_KEY_PATH),
  }],
  insecureSkipTLSVerify: true
};

/** Indicates whether the test has completed. @type {boolean} */
let testCompleted = false;

/**
 * k6 `setup()` lifecycle function.
 *
 * Randomizes resource IDs and distributes them across virtual users.
 *
 * @returns {{
 *   callbackChunks: Array<Array<string|{id:string}>>,
 *   totalCallbacks: number,
 *   callbackCount: number,
 *   allCompleted: boolean
 * }}
 */
export function setup() {
  shuffleArray(resourceIds);
  const callbackChunks = distributeItemsAmongGroups(resourceIds, VU_COUNT_SET);

  console.log(`Callbacks distributed among ${VU_COUNT_SET} virtual users:`);
  for (let i = 0; i < VU_COUNT_SET; i++) {
    console.log(`- VU #${i + 1}: ${callbackChunks[i].length} callbacks`);
  }

  return {
    callbackChunks,
    totalCallbacks: resourceIds.length,
    callbackCount: 0,
    allCompleted: false
  };
}

/**
 * Scenario execution function.
 *
 * Each virtual user processes its assigned RTP callbacks and sends
 * HTTP POST requests to the callback cancel endpoint.
 *
 /**
 * @param {{
 *  callbackChunks: Array<Array<any>>,
 *  totalCallbacks: number,
 *  callbackCount: number,
 *  allCompleted: boolean,
 *  currentIndices?: Record<number, number>,
 *  vuCallbackCount?: Record<number, number>,
 *  vuCallbacked?: Record<number, boolean>
 * }} data Setup data shared across VUs.
 *
 * @returns {Object} HTTP response or synthetic response when idle.
 */
export function callbackCancel(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: String(Math.floor(elapsedSeconds / 10) * 10),
    stage: determineStage(elapsedSeconds),
    callbackCount: String(data.callbackCount),
    vu: String(__VU)
  };

  currentRPS.add(1, tags);

  if (testCompleted) {
    console.log(`⏹️ Test completed. VU #${__VU} idling...`);
    sleep(30);
    return { status: 200, message: 'Test completed', noMetrics: true };
  }

  const vuIndex = __VU - 1;
  if (!data.callbackChunks[vuIndex]) {
    console.log(`⚠️ VU #${__VU}: No chunk assigned.`);
    return { status: 400, message: 'No chunk', noMetrics: true };
  }

  const myCallbacks = data.callbackChunks[vuIndex];

  if (!data.currentIndices) data.currentIndices = {};
  if (!data.currentIndices[vuIndex]) data.currentIndices[vuIndex] = 0;
  if (!data.vuCallbackCount) data.vuCallbackCount = {};
  if (!data.vuCallbackCount[vuIndex]) data.vuCallbackCount[vuIndex] = 0;

  if (data.vuCallbackCount[vuIndex] >= myCallbacks.length) {
    console.log(`✓ VU #${__VU}: Completed ${myCallbacks.length} callbacks.`);
    sleep(5);
    return { status: 200, message: 'VU done', noMetrics: true };
  }

  const currentIndex = data.currentIndices[vuIndex];

  const callbackItem = myCallbacks[currentIndex];
  const resourceId = callbackItem?.id || callbackItem;

  if (data.currentIndices[vuIndex] in (data.vuCallbacked || {})) {
    data.currentIndices[vuIndex] = (currentIndex + 1) % myCallbacks.length;
    return callbackCancel(data);
  }

  const headers = { 'Content-Type': 'application/json' };
  const url = endpoints.callbackCancel;
  const payload = buildCallbackCancelPayload(resourceId, RTP_SP_ID);

  const start = Date.now();
  const res = http.post(url, JSON.stringify(payload), { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status >= 200 && res.status < 300) {
    successCounter.add(1, tags);
    data.vuCallbackCount[vuIndex]++;
    data.callbackCount++;

    if (!data.vuCallbacked) data.vuCallbacked = {};
    data.vuCallbacked[data.currentIndices[vuIndex]] = true;

    if (data.callbackCount % 50 === 0 || data.vuCallbackCount[vuIndex] === myCallbacks.length) {
      console.log(`✓ VU #${__VU}: ${data.vuCallbackCount[vuIndex]}/${myCallbacks.length} done (Total: ${data.callbackCount}/${data.totalCallbacks}) | ID: ${resourceId.slice(0,8)}...`);
    }

    if (data.callbackCount >= data.totalCallbacks && !data.allCompleted) {
      data.allCompleted = true;
      testCompleted = true;
      console.log(`✅ ALL ${data.totalCallbacks} CALLBACKS DONE! (${Math.round(elapsedSeconds)}s)`);
      return { status: 200, message: 'Test done', noMetrics: false };
    }
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Callback failed ID=${resourceId?.slice(0,8)}...: ${res.status} | ${res.body?.slice(0,100)}`);
  }

  check(res, { 'callback 2xx': (r) => r.status >= 200 && r.status < 300 });

  data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % myCallbacks.length;
  if (SLEEP_ITER > 0) sleep(SLEEP_ITER);

  return res;
}
