import http from 'k6/http';
import { check, sleep } from 'k6';
import { endpoints, determineStage, getOptions} from "../../utils/utils.js";
import { createStandardMetrics } from "../../utils/metrics-utils.js";
import { shuffleArray, distributeItemsAmongGroups} from "../../utils/batch-utils.js";
import { createHandleSummary } from "../../utils/summary-utils.js";
import { buildCallbackPayload } from "../../utils/sender-payloads.js";
import { createCallbackTeardown } from "../../utils/teardown-utils.js";

const START_TIME = Date.now();
const VU_COUNT_SET = __ENV;
const MTLS_CERT_PATH = '../../utils/certificates/cert.pem';
const MTLS_KEY_PATH  = '../../utils/certificates/key-unencrypted.pem';
const resourceIds = JSON.parse(open('../../script/resourceIds.json'));
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export let options = {
    ...getOptions('stress_test_fixed_user', 'callback'),
    setupTimeout: '5m',
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT_SET,
            iterations: resourceIds.length,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'callback'
        }
    },

    tlsAuth: [
        {
            domains: ['api-rtp-cb.dev.cstar.pagopa.it'],
            cert: open(MTLS_CERT_PATH),
            key: open(MTLS_KEY_PATH),
        }
    ],

    insecureSkipTLSVerify: true
};

let testCompleted = false;

export function setup() {

    const wrappedIds = resourceIds.map(r => ({ id: String(r), processed: false }));

    shuffleArray(wrappedIds);
    const callbackChunks = distributeItemsAmongGroups(wrappedIds, VU_COUNT_SET);

    console.log(`Callback distributed among ${VU_COUNT_SET} virtual users:`);
    for (let i = 0; i < VU_COUNT_SET; i++) {
        console.log(`- VU #${i + 1}: ${callbackChunks[i].length} callback`);
    }

    return {
        callbackChunks: callbackChunks,
        totalCallback: wrappedIds.length,
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
    const myCallback = data.callbackChunks[vuIndex];

    if (!myCallback) {
        console.log(`⚠️ VU #${__VU}: No callback chunk assigned. Termination.`);
        return { status: 400, message: 'No callback chunk assigned', noMetrics: true };
    }

    if (!data.currentIndices) data.currentIndices = {};
    if (data.currentIndices[vuIndex] === undefined) data.currentIndices[vuIndex] = 0;

    if (!data.vuCallbackCount) data.vuCallbackCount = {};
    if (data.vuCallbackCount[vuIndex] === undefined) data.vuCallbackCount[vuIndex] = 0;

    if (data.vuCallbackCount[vuIndex] >= myCallback.length) {
        console.log(`✓ VU #${__VU}: Completed all ${myCallback.length} callbacks assigned.`);
        sleep(5);
        return { status: 200, message: `VU #${__VU} completed`, noMetrics: true };
    }

    const currentIndex = data.currentIndices[vuIndex];
    const callbackItem = myCallback[currentIndex];

    if (callbackItem.processed) {
        data.currentIndices[vuIndex] = (currentIndex + 1) % myCallback.length;
        return callback(data);
    }

    const id = callbackItem.id;
    const payload = JSON.stringify(buildCallbackPayload(id));

    const headers = {'Content-Type': 'application/json'};
    const url = endpoints.callbackSend;

    const start = Date.now();
    const res = http.post(url, payload, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    if (res.status >= 200 && res.status < 300) {
        successCounter.add(1, tags);

        callbackItem.processed = true;
        data.vuCallbackCount[vuIndex]++;
        data.callbackCount++;

        if (data.callbackCount % 50 === 0 || data.vuCallbackCount[vuIndex] === myCallback.length) {
            console.log(`✓ VU #${__VU}: ${data.vuCallbackCount[vuIndex]}/${myCallback.length} callback (Total: ${data.callbackCount}/${data.totalCallback})`);
        }

        if (data.callbackCount >= data.totalCallback && !data.allCompleted) {
            data.allCompleted = true;
            testCompleted = true;
            console.log(`✅ TEST COMPLETED: All ${data.totalCallback} callback have been processed!`);
            console.log(`Total execution time: ${Math.round(elapsedSeconds)} seconds`);
            return { status: 200, message: 'Test completed successfully', noMetrics: false };
        }
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${__VU}: Failed callback for ID ${id}: Status ${res.status}`);
    }

    check(res, { 'callback: status is 2xx': (r) => r.status >= 200 && r.status < 300 });

    data.currentIndices[vuIndex] = (currentIndex + 1) % myCallback.length;
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