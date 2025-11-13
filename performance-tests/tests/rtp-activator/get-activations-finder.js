import http from 'k6/http';
import {check} from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, getOptions} from '../../utils/utils.js';
import {createStandardMetrics} from '../../utils/metrics-utils.js';
import {createHandleSummary} from '../../utils/summary-utils.js';
import {createFindAllByServiceProviderTeardown} from '../../utils/teardown-utils.js';

/**
 * @file Find All Activations by Service Provider — Stress Test (k6)
 * @description
 * Executes high-throughput paged GET requests to fetch activations belonging to a
 * single Service Provider. Uses the vendor-specific `NextActivationId` request header
 * to continue pagination across calls on a per-VU basis.
 *
 * ## Inputs
 * - Environment variables:
 * - `VU_COUNT_SET` (number, default: 7) — virtual users.
 * - `ITERATIONS` (number, default: 20000) — total shared iterations across all VUs.
 *
 * ## Behavior
 * - `setup()` authenticates and returns an access token.
 * - Each VU maintains its own pagination cursor in `nextIds[vu]`.
 * - A response with HTTP 200 increments success; other statuses increment failures.
 *
 * ## Outputs
 * - `handleSummary` produces aggregated reports via `createHandleSummary`.
 */

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Number of virtual users. */
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 7;

/** Total shared iterations. */
const ITERATIONS = Number(__ENV.ITERATIONS) || 20000;

/**
 * Standard custom metrics used by this test.
 * @typedef {Object} StandardMetrics
 * @property {import('k6/metrics').Rate} currentRPS
 * @property {import('k6/metrics').Counter} failureCounter
 * @property {import('k6/metrics').Counter} successCounter
 * @property {import('k6/metrics').Trend} responseTimeTrend
 */
const {currentRPS, failureCounter, successCounter, responseTimeTrend} = createStandardMetrics();

/**
 * Mutable reference used by teardown/summary utilities to observe completion state.
 * @type {{ value: boolean }}
 */
const testCompletedRef = {value: false};

/**
 * k6 options and scenario configuration.
 *
 * @type {import('k6/options').Options}
 */
export let options = {
    ...getOptions('stress_test_fixed_user', 'findAllByServiceProvider'),
    setupTimeout: '5m',
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: ITERATIONS,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'findAllByServiceProvider'
        }
    }
};

/**
 * @typedef {Object} SetupData
 * @property {string} access_token OAuth access token to call the API.
 */


/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates and returns the access token for use in the test body.
 *
 * @returns {SetupData} An object containing the `access_token`.
 */
export function setup() {
    const auth = setupAuth();

    return {
        access_token: auth.access_token
    };
}

/**
 * Per-VU pagination cursor map. Keys are VU numbers and values are the last
 * `nextActivationId` observed (or `null` if paging ended for that VU).
 * @type {Record<number, string | null | undefined>}
 */
const nextIds = {};

/**
 * Test body executed by each VU.
 *
 * Builds the request headers (including `NextActivationId` when present), performs a paged GET
 * to the activations endpoint, records metrics, and updates the per-VU pagination cursor.
 *
 * @param {SetupData} data Setup data returned by `setup()`.
 * @returns {import('k6/http').RefinedResponse<'text'>} The HTTP response from k6.
 */
export function findAllByServiceProvider(data) {
    const vu = __VU;
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds),
        vu
    };

    currentRPS.add(1, tags);

    const headers = buildHeaders(data.access_token);
    const nextActivationId = nextIds[vu];
    if (nextActivationId !== undefined && nextActivationId !== null) {
        headers['NextActivationId'] = nextActivationId;
    }

    const size = 128;
    const url = `${endpoints.activations}?size=${size}`;
    const start = Date.now();
    const res = http.get(url, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    check(res, {
        'find: status is 200': (r) => r.status === 200
    });

    if (res.status === 200) {
        let body;
        try {
            body = res.json();
        } catch (error) {
            console.error(`❌ VU #${vu}: Failed to parse JSON body (Status ${res.status}): ${error.message}`);

            failureCounter.add(1, tags);
            return;
        }

        if (!body?.activations || body.activations.length === 0) {
            console.log(`VU #${vu}: received empty page`);
            nextIds[vu] = null;
        } else {
            nextIds[vu] = body.metadata?.nextActivationId || null;
            successCounter.add(1, tags);
        }
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${vu}: Failed GET: Status ${res.status}`);
    }

    return res;
}

/**
 * k6 `teardown` export produced by the finder-specific teardown factory.
 */
export const teardown = createFindAllByServiceProviderTeardown({
    START_TIME,
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});

/**
 * k6 `handleSummary` export created by a summary factory.
 */
export const handleSummary = createHandleSummary({
    START_TIME,
    testName: 'GetAllActivationsByServiceProvider STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'findAllByServiceProvider',
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});
