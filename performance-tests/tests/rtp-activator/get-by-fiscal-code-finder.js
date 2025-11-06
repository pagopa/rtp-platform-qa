import http from 'k6/http';
import { check, sleep } from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials} from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { shuffleArray } from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createFinderTeardown } from '../../utils/teardown-utils.js';

// === CONFIG ===
const START_TIME = Date.now();
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 15;
const ITERATIONS = Number(__ENV.ITERATIONS) || 45000;
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

// === LOAD DATA ===
const activationIds = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activations.json'))
        .map(r => r?.fiscalCode)
        .filter(fc => fc != null && fc !== '')
)).map(String);
const wrappedActivations = activationIds.map(fiscalCode => ({ fiscalCode }));

// === METRICS ===
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

// === K6 OPTIONS ===
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

let testCompleted = false;

// === HELPER ===
function randomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

// === SETUP ===
export function setup() {
    const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);

    shuffleArray(wrappedActivations);
    console.log(`✅ Loaded ${wrappedActivations.length} fiscal codes for GET test.`);

    return {
        access_token: auth.access_token,
        wrappedActivations,
    };
}

// === MAIN TEST FUNCTION ===
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

    // === CHECK AND METRICS ===
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

const testCompletedRef = { testCompleted: false };

// === TEARDOWN ===
export const teardown = createFinderTeardown({
    START_TIME,
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});

Object.defineProperty(testCompletedRef, 'value', {
    get: () => testCompleted,
    set: (newValue) => { testCompleted = newValue; }
});

// === SUMMARY ===
export const handleSummary = createHandleSummary({
    START_TIME,
    testName: 'MULTI-VU GETBYFISCALCODE STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'fiscalcode',
    VU_COUNT: VU_COUNT_SET
});
