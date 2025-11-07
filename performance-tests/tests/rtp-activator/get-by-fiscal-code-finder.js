import http from 'k6/http';
import { check, sleep } from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials} from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { shuffleArray } from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createFinderTeardown } from '../../utils/teardown-utils.js';

/**
 * @file Multi-VU "GET by Fiscal Code" Stress Test (k6)
 * @description
 * Issues high-throughput GET requests to the finder endpoint, setting the `PayerId` header
 * with a random fiscal code selected from an input JSON. Work is distributed across VUs using
 * a shared-iterations executor. Standard metrics (success/failure counters, RPS rate, response time trend)
 * are collected and tagged by time window and derived stage.
 *
 * ## Inputs
 * - JSON input: `../../json-file/rtp-activator/activations.json` (objects containing `fiscalCode`).
 * - Environment variables:
 * - `VU_COUNT_SET` (number, default: 15): number of virtual users.
 * - `ITERATIONS` (number, default: 45000): total iterations across all VUs.
 * - `SLEEP_ITER` (number, seconds, default: 0): optional sleep after each iteration.
 *
 * ## Outputs
 * - `handleSummary` produces aggregated reports via `createHandleSummary` (HTML/JSON as configured).
 */

/** Start timestamp (ms) for run-level timing. */
const START_TIME = Date.now();

/** Number of VUs, configurable via env. */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 15;

/** Total shared iterations for the scenario. */
const ITERATIONS = Number(__ENV.ITERATIONS) || 45000;

/** Optional per-iteration sleep time (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/**
 * Load unique fiscal codes from the input JSON and prepare a wrapped structure.
 *
 * @type {string[]} activationIds Unique list of fiscal codes as strings.
 */
const activationIds = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activations.json'))
        .map(r => r?.fiscalCode)
        .filter(fc => fc != null && fc !== '')
)).map(String);

/**
 * Each entry provides a `fiscalCode` property used to set the `PayerId` header per request.
 * @type {Array<{ fiscalCode: string }>} wrappedActivations
 */
const wrappedActivations = activationIds.map(fiscalCode => ({ fiscalCode }));

/**
 * Standard metrics exposed by the metrics utility.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate} currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend} responseTimeTrend
 */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * k6 options using a shared-iterations scenario. The test body is `findByFiscalCode`.
 *
 * @type {import('k6/options').Options}
 */
export let options = {
    ...getOptions('stress_test_fixed_user', 'findByFiscalCode'),
    setupTimeout: '5m',
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: ITERATIONS,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'findByFiscalCode'
        }
    }
};

/**
 * Global flag signaling the test has logically completed.
 * When true, workers can idle to keep the dashboard available.
 * @type {boolean}
 */
let testCompleted = false;

/**
 * Returns a random item from a non-empty array.
 *
 * @template T
 * @param {T[]} arr Array to pick from.
 * @returns {T} A randomly selected element.
 */
function randomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * @typedef {Object} SetupData
 * @property {string} access_token OAuth access token to call the API.
 * @property {Array<{ fiscalCode: string }>} wrappedActivations Shuffled pool of fiscal codes.
 */


/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER`, shuffles the list of fiscal codes, and returns
 * the shared dataset to be used by VUs during execution.
 *
 * @returns {SetupData} Token and the activation pool used by `findByFiscalCode`.
 */
export function setup() {
    const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);

    shuffleArray(wrappedActivations);
    console.log(`✅ Loaded ${wrappedActivations.length} fiscal codes for GET test.`);

    return {
        access_token: auth.access_token,
        wrappedActivations,
    };
}

/**
 * Test body executed by each VU.
 *
 * Picks a random fiscal code, sets the `PayerId` header, performs a GET on the configured endpoint,
 * and records metrics. Success is defined as HTTP 200; otherwise it increments the failure counter.
 *
 * @param {SetupData} data Shared data produced by `setup()`.
 * @returns {import('k6/http').RefinedResponse<'text'>} The HTTP response object from k6.
 */
export function findByFiscalCode(data) {
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds),
        vu: __VU
    };

    currentRPS.add(1, tags);

    const headers = buildHeaders(data.access_token);
    const picked = randomItem(data.wrappedActivations);
    const fiscalCode = picked?.fiscalCode;
    headers['PayerId'] = fiscalCode;

    const url = endpoints.getByFiscalCode;
    const start = Date.now();
    const res = http.get(url, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    check(res, {
        'findByFiscalCode: status is 200': (r) => r.status === 200,
    });

    if (res.status === 200) {
        successCounter.add(1, tags);
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${__VU}: Failed GET for fiscalCode ${fiscalCode}: Status ${res.status}`);
    }

    if (SLEEP_ITER > 0) {
        sleep(SLEEP_ITER);
    }

    return res;
}

/**
 * Small helper that exposes `testCompleted` as a mutable reference for teardown utilities.
 * The property descriptor ensures reads/writes affect the module-scoped variable above.
 */
const testCompletedRef = { testCompleted: false };
export const teardown = createFinderTeardown({
    START_TIME,
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});

/**
 * k6 `teardown` export created via a specialized utility for finder tests.
 *
 * It forwards finder-specific fields to the generic batch-processing teardown
 * and logs a concise end-of-test summary.
 */
Object.defineProperty(testCompletedRef, 'value', {
    get: () => testCompleted,
    set: (newValue) => { testCompleted = newValue; }
});

/**
 * k6 `handleSummary` export created by a summary factory.
 *
 * Produces HTML/JSON summaries with a consistent naming scheme and derives completion
 * state from global variables or metrics when available.
 */
export const handleSummary = createHandleSummary({
    START_TIME,
    testName: 'MULTI-VU GETBYFISCALCODE STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'fiscalcode',
    VU_COUNT: VU_COUNT_SET
});
