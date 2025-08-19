import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials } from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import {shuffleArray, distributeItemsAmongGroups, createSendInBatch} from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';

const START_TIME = Date.now();
const { SERVICE_PROVIDER_ID } = __ENV;
const VU_COUNT_SET = 50;

const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export let options = {
    ...getOptions('stress_test_fixed_user', 'callback'),
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: 500,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'callback'
        }
    }
};

let testCompleted = false;

export function setup() {
    const auth = setupAuth(ActorCredentials.CREDITOR_SERVICE_PROVIDER);

    const resourceIds = createSendInBatch({
        accessToken: auth.access_token,
        targetActivations: 500,
        batchSize: 50,
        delayBetweenBatches: 2,
        serviceProviderId: SERVICE_PROVIDER_ID
    });

    shuffleArray(resourceIds)

    const callbackChunks = distributeItemsAmongGroups(resourceIds, VU_COUNT_SET);

    console.log(`Callback distributed among ${VU_COUNT_SET} virtual users:`);
    for (let i = 0; i < VU_COUNT_SET; i++) {
        console.log(`- VU #${i + 1}: ${callbackChunks[i].length} callback`);
    }

    return {
        access_token: auth.access_token,
        callbackChunks: callbackChunks,
        totalCallback: resourceIds.length,
        callbackCount: 0,
        allCompleted: false
    };
}

export function callback(data){
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds),
        callbackCount: data.callbackCount,
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

    if (!data.callbackChunks[vuIndex]) {
        console.log(`⚠️ VU #${__VU}: No callback chunk assigned. Termination.`);
        return { status: 400, message: 'No callback chunk assigned', noMetrics: true };
    }

    const myCallback = data.callbackChunks[vuIndex];

    if (data.currentIndices === undefined) {
        data.currentIndices = {};
    }
    if (data.currentIndices[vuIndex] === undefined) {
        data.currentIndices[vuIndex] = 0;
    }

    if (data.vuCallbackCount === undefined) {
        data.vuCallbackCount = {};
    }
    if (data.vuCallbackCount[vuIndex] === undefined) {
        data.vuCallbackCount[vuIndex] = 0;
    }

    if (data.vuCallbackCount[vuIndex] >= myCallback.length) {
        console.log(`✓ VU #${__VU}: Completed all ${myCallback.length} deactivations assigned.`);
        sleep(5);
        return {
            status: 200,
            message: `VU #${__VU} completed all deactivations, idle for dashboard`,
            noMetrics: true
        };
    }

    const currentIndex = data.currentIndices[vuIndex];
    const callbackItem = myCallback[currentIndex];

    if (callbackItem.processed) {
        data.currentIndices[vuIndex] = (currentIndex + 1) % myCallback.length;
        return callback(data);
    }

    const headers = {
        'Content-Type': 'application/json'
    };
    const url = endpoints.callbackSend

    const start = Date.now();
    const res = http.post(url, null, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    if (res.status === 200) {
        successCounter.add(1, tags);

        callbackItem.processed = true;
        data.vuCallbackCount[vuIndex]++;
        data.vuCallbackCount++;

        if (data.vuCallbackCount % 50 === 0 || data.vuCallbackCount[vuIndex] === data.callbackChunks[vuIndex].length) {
            console.log(`✓ VU #${__VU}: ${data.callbackCount[vuIndex]}/${data.callbackChunks[vuIndex].length} callback completed (Total: ${data.callbackCount}/${data.totalCallback})`);
        }

    }

    if (data.callbackCount >= data.totalCallback && !data.allCompleted) {
        data.allCompleted = true;
        testCompleted = true;
        console.log(`✅ TEST COMPLETED: All ${data.totalCallback} callback have been processed!`);
        console.log(`Total execution time: ${Math.round(elapsedSeconds)} seconds`);
        console.log(`Dashboard will remain active for viewing results.`);
        return {
            status: 200,
            message: 'Test completed successfully, dashboard still active',
            noMetrics: false
        };
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${__VU}: Failed callback for ID ${callbackItem.id}: Status ${res.status}`);
    }

    check(res, {
        'callback: status is 200': (r) => r.status === 200
    });

    data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % myCallback.length;

    sleep(1)

    return res;
}

const testCompletedRef = { value: false };

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