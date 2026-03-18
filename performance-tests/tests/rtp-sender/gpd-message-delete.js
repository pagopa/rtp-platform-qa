import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { shuffleArray, distributeItemsAmongGroups } from '../../utils/batch-utils.js';
import {
  buildHeaders,
  endpoints,
  determineStage,
  getOptions,
  setupAuth,
  ActorCredentials
} from '../../utils/utils.js';
import { buildDeleteGpdMessagePayload } from "../../utils/sender-payloads.js";

/**
 * @file GPD Message Delete Stress Test (k6) - Distributed VU Version
 * @description
 * Deletes previously created GPD messages using operation IDs loaded from file.
 * Operation IDs are distributed evenly among virtual users (VUs) for parallel execution.
 *
 * ## Flow
 * 1. Load operation IDs from JSON file.
 * 2. Shuffle IDs to avoid sequential patterns.
 * 3. Distribute IDs evenly among VUs.
 * 4. Each VU processes its assigned operation IDs sequentially.
 *
 * ## Input file
 * `json-file/rtp-sender/gpd-message-id.json`
 */

const START_TIME = Date.now();

/** Number of virtual users (`VU_COUNT_SET`, default: 10). @type {number} */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

/** Optional sleep between iterations in seconds (`SLEEP_ITER`). @type {number} */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/**
 * Operation IDs loaded from file.
 * @type {string[]}
 */
const operationIds = Array.from(
    new Set(JSON.parse(open('../../json-file/rtp-sender/gpd-message-id.json')))
).map(String);

/**
 * Standard performance metrics used in the test.
 */
const {
  currentRPS,
  failureCounter,
  successCounter,
  responseTimeTrend,
} = createStandardMetrics();

/**
 * k6 test configuration.
 */
export const options = {
  ...getOptions('stress_test_fixed_user', 'deleteMessage'),
  setupTimeout: '2m',
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: operationIds.length,
      maxDuration: '240m',
      gracefulStop: '30s',
      exec: 'deleteMessage',
    },
  },
};

/** Indicates whether the test has completed. @type {boolean} */
let testCompleted = false;

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates and distributes operation IDs across virtual users.
 *
 * @returns {{
 *   operationIdChunks: Array<Array<string>>,
 *   totalOperations: number,
 *   deleteCount: number,
 *   allCompleted: boolean
 * }}
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.RTP_CONSUMER);
  const accessToken = auth.access_token;

  shuffleArray(operationIds);
  const operationIdChunks = distributeItemsAmongGroups(operationIds, VU_COUNT_SET);

  console.log(`Operation IDs distributed among ${VU_COUNT_SET} virtual users:`);
  for (let i = 0; i < VU_COUNT_SET; i++) {
    console.log(`- VU #${i + 1}: ${operationIdChunks[i].length} operation IDs`);
  }

  console.log(`Loaded ${operationIds.length} operationIds for delete test.`);

  return {
    operationIdChunks,
    accessToken,
    totalOperations: operationIds.length,
    deleteCount: 0,
    allCompleted: false
  };
}

/**
 * Scenario execution function.
 *
 * Each virtual user processes its assigned operation IDs sequentially,
 * sending HTTP POST requests to delete GPD messages.
 *
 * @param {{
 *   operationIdChunks: Array<Array<string>>,
 *   accessToken: string,
 *   totalOperations: number,
 *   deleteCount: number,
 *   allCompleted: boolean,
 *   currentIndices?: Record<number, number>,
 *   vuDeleteCount?: Record<number, number>,
 *   vuDeleted?: Record<number, boolean>
 * }} data Setup data shared across VUs.
 *
 * @returns {Object} HTTP response or synthetic response when idle.
 */
export function deleteMessage(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: String(Math.floor(elapsedSeconds / 10) * 10),
    stage: determineStage(elapsedSeconds),
    deleteCount: String(data.deleteCount),
    vu: String(__VU)
  };

  currentRPS.add(1, tags);

  if (testCompleted) {
    console.log(`⏹️ Test completed. VU #${__VU} idling...`);
    sleep(30);
    return { status: 200, message: 'Test completed', noMetrics: true };
  }

  const vuIndex = __VU - 1;
  if (!data.operationIdChunks[vuIndex]) {
    console.warn(`⚠️ VU #${__VU}: No chunk assigned.`);
    return { status: 400, message: 'No chunk', noMetrics: true };
  }

  const myOperationIds = data.operationIdChunks[vuIndex];

  if (!data.currentIndices) data.currentIndices = {};
  if (!data.currentIndices[vuIndex]) data.currentIndices[vuIndex] = 0;
  if (!data.vuDeleteCount) data.vuDeleteCount = {};
  if (!data.vuDeleteCount[vuIndex]) data.vuDeleteCount[vuIndex] = 0;

  if (data.vuDeleteCount[vuIndex] >= myOperationIds.length) {
    console.log(`✓ VU #${__VU}: Completed ${myOperationIds.length} deletes.`);
    sleep(5);
    return { status: 200, message: 'VU done', noMetrics: true };
  }

  const currentIndex = data.currentIndices[vuIndex];
  const operationId = myOperationIds[currentIndex];

  if (!operationId) {
    console.warn(`⚠️ VU #${__VU}: No operationId found for iteration ${currentIndex}.`);
    data.currentIndices[vuIndex] = (currentIndex + 1) % myOperationIds.length;
    return { status: 400, message: 'No operationId', noMetrics: true };
  }

  if (data.currentIndices[vuIndex] in (data.vuDeleted || {})) {
    data.currentIndices[vuIndex] = (currentIndex + 1) % myOperationIds.length;
    return deleteMessage(data);
  }

  const payload = buildDeleteGpdMessagePayload(operationId);
  const headers = {
    ...buildHeaders(data.accessToken),
    'Idempotency-Key': uuidv4(),
  };

  const start = Date.now();
  const res = http.post(
      endpoints.gpdMessage,
      JSON.stringify(payload),
      { headers }
  );
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status >= 200 && res.status < 300) {
    successCounter.add(1, tags);
    data.vuDeleteCount[vuIndex]++;
    data.deleteCount++;

    if (!data.vuDeleted) data.vuDeleted = {};
    data.vuDeleted[data.currentIndices[vuIndex]] = true;

    if (data.deleteCount % 50 === 0 || data.vuDeleteCount[vuIndex] === myOperationIds.length) {
      console.log(
          `✓ VU #${__VU}: ${data.vuDeleteCount[vuIndex]}/${myOperationIds.length} done ` +
          `(Total: ${data.deleteCount}/${data.totalOperations}) | ID: ${operationId.slice(0,8)}...`
      );
    }

    if (data.deleteCount >= data.totalOperations && !data.allCompleted) {
      data.allCompleted = true;
      testCompleted = true;
      console.log(`✅ ALL ${data.totalOperations} DELETES DONE! (${Math.round(elapsedSeconds)}s)`);
      return { status: 200, message: 'Test done', noMetrics: false };
    }
  } else {
    failureCounter.add(1, tags);
    console.error(
        `❌ VU #${__VU}: delete failed for operationId ${operationId.slice(0,8)}...: ` +
        `${res.status} | ${res.body?.slice(0, 200)}`
    );
  }

  check(res, {
    'delete message 2xx': (r) => r.status >= 200 && r.status < 300,
  });

  data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % myOperationIds.length;

  if (SLEEP_ITER > 0) sleep(SLEEP_ITER);

  return res;
}
