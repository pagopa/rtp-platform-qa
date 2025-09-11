import http from 'k6/http';
import { check } from 'k6';
import { setupAuth, buildHeaders, endpoints, determineStage, getOptions } from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationsInBatch } from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createFinderTeardown } from '../../utils/teardown-utils.js';

const START_TIME = Date.now();
const { DEBTOR_SERVICE_PROVIDER_ID } = __ENV;
const VU_COUNT_SET = 500;

const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export let options = {
    ...getOptions('stress_test_fixed_user', 'findByFiscalCode'),
    setupTimeout: '5m',
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: 50000,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'findByFiscalCode'
        }
    }
};

let testCompleted = false;

export function setup() {
    const auth = setupAuth();

    const activationFiscalCodes = createActivationsInBatch({
        accessToken: auth.access_token,
        targetActivations: 2000,
        batchSize: 100,
        delayBetweenBatches: 2,
        serviceProviderId: DEBTOR_SERVICE_PROVIDER_ID
    });

    const fiscalCodes = activationFiscalCodes.map(a => a.fiscalCode);

    console.log(`✅ Created ${fiscalCodes.length} activations.`);

    return {
        access_token: auth.access_token,
        fiscalCodes
    };
}

function randomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

export function findByFiscalCode(data) {
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds),
        vu: __VU
    };

    currentRPS.add(1, tags);

    const fiscalCode = randomItem(data.fiscalCodes);

    const headers = buildHeaders(data.access_token);
    headers['PayerId'] = fiscalCode;

    const url = endpoints.getByFiscalCode;
    const start = Date.now();
    const res = http.get(url, null, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    check(res, {
        'find: status is 200': (r) => r.status === 200
    });

    if (res.status === 200) {
        successCounter.add(1, tags);
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${__VU}: Failed GET for fiscalCode ${fiscalCode}: Status ${res.status}`);
    }

    return res;
}

const testCompletedRef = { testCompleted: false };

export const teardown = createFinderTeardown({
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
    testName: 'MULTI-VU GETBYFISCALCODE STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'fiscalcode',
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});
