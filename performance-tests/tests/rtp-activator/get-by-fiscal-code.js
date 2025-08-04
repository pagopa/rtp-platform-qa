import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, endpoints, determineStage, getOptions } from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationsInBatch, shuffleArray, distributeItemsAmongGroups } from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createFinderTeardown } from '../../utils/teardown-utils.js';

const START_TIME = Date.now();
const { DEBTOR_SERVICE_PROVIDER_ID } = __ENV;
const VU_COUNT_SET = 50;

const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export let options = {
    ...getOptions('stress_test_fixed_user', 'findByFiscalCode'),
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: 500,
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
        targetActivations: 500,
        batchSize: 50,
        delayBetweenBatches: 2,
        serviceProviderId: DEBTOR_SERVICE_PROVIDER_ID
    });

    shuffleArray(activationFiscalCodes);
    const activationChunks = distributeItemsAmongGroups(activationFiscalCodes, VU_COUNT_SET);

    console.log(`Activations distributed among ${VU_COUNT_SET} virtual users:`);
    for (let i = 0; i < VU_COUNT_SET; i++) {
        console.log(`- VU #${i + 1}: ${activationChunks[i].length} activations`);
    }

    sleep(60);

    return {
        access_token: auth.access_token,
        activationChunks,
        totalActivations: activationFiscalCodes.length,
        requestCount: 0,
        allCompleted: false
    };
}

export function findByFiscalCode(data) {
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds),
        requestCount: data.requestCount,
        vu: __VU
    };

    currentRPS.add(1, tags);

    if (testCompleted) {
        console.log(`⏹️ Test already completed. VU #${__VU} staying idle to keep dashboard active...`);
        sleep(30);
        return {
            status: 200,
            message: 'Test already completed, waiting for dashboard viewing',
            noMetrics: true
        };
    }

    const vuIndex = __VU - 1;
    const myActivations = data.activationChunks[vuIndex];

    if (!myActivations) {
        console.log(`⚠️ VU #${__VU}: No activation chunk assigned. Termination.`);
        return { status: 400, message: 'No activation chunk assigned', noMetrics: true };
    }

    data.currentIndices = data.currentIndices || {};
    data.vuRequestCount = data.vuRequestCount || {};

    data.currentIndices[vuIndex] = data.currentIndices[vuIndex] || 0;
    data.vuRequestCount[vuIndex] = data.vuRequestCount[vuIndex] || 0;

    if (data.vuRequestCount[vuIndex] >= myActivations.length) {
        console.log(`✓ VU #${__VU}: Completed all ${myActivations.length} GETs assigned.`);
        sleep(5);
        return {
            status: 200,
            message: `VU #${__VU} completed all GETs, idle for dashboard`,
            noMetrics: true
        };
    }

    const currentIndex = data.currentIndices[vuIndex];
    const activationItem = myActivations[currentIndex];

    if (activationItem.finded) {
        data.currentIndices[vuIndex] = (currentIndex + 1) % myActivations.length;
        return findByFiscalCode(data);
    }

    const headers = buildHeaders(data.access_token);
    headers['PayerId'] = activationItem.fiscalCode;

    const url = endpoints.getByFiscalCode;
    const start = Date.now();
    const res = http.get(url, null, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    check(res, {
        'find: status is 204': (r) => r.status === 204
    });

    if (res.status === 204) {
        successCounter.add(1, tags);
        activationItem.finded = true;
        data.vuRequestCount[vuIndex]++;
        data.requestCount++;

        if (
            data.requestCount % 50 === 0 ||
            data.vuRequestCount[vuIndex] === myActivations.length
        ) {
            console.log(`✓ VU #${__VU}: ${data.vuRequestCount[vuIndex]}/${myActivations.length} GETs completed (Total: ${data.requestCount}/${data.totalActivations})`);
        }

        if (data.requestCount >= data.totalActivations && !data.allCompleted) {
            data.allCompleted = true;
            testCompleted = true;
            console.log(`✅ TEST COMPLETED: All ${data.totalActivations} GETs have been performed!`);
            console.log(`Total execution time: ${Math.round(elapsedSeconds)} seconds`);
            console.log(`Dashboard will remain active for viewing results.`);
            return {
                status: 204,
                message: 'Test completed successfully, dashboard still active',
                noMetrics: false
            };
        }
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${__VU}: Failed GET for fiscalCode ${activationItem.fiscalCode}: Status ${res.status}`);
    }

    data.currentIndices[vuIndex] = (currentIndex + 1) % myActivations.length;
    sleep(1);
    return res;
}

const testCompletedRef = { value: false };

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
    VU_COUNT: VU_COUNT_SET
});