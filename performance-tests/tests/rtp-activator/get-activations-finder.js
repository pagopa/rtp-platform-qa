import http from 'k6/http';
import {check} from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, getOptions} from '../../utils/utils.js';
import {createStandardMetrics} from '../../utils/metrics-utils.js';
import {createHandleSummary} from '../../utils/summary-utils.js';
import {createFindAllByServiceProviderTeardown} from '../../utils/teardown-utils.js';

const START_TIME = Date.now();
const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 7;
const ITERATIONS = Number(__ENV.ITERATIONS) || 20000;

const {currentRPS, failureCounter, successCounter, responseTimeTrend} = createStandardMetrics();

const testCompletedRef = {value: false};

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

export function setup() {
    const auth = setupAuth();

    return {
        access_token: auth.access_token
    };
}

const nextIds = {};

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
    if (nextIds[vu]) headers['NextActivationId'] = nextIds[vu];

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
        const body = res.json();
        if (!body?.activations || body.activations.length === 0) {
            console.log(`VU #${vu}: received empty page`);
            nextIds[vu] = null;
        } else {
            nextIds[vu] = body?.metadata?.nextActivationId || null;
        }
        successCounter.add(1, tags)
    } else {
        failureCounter.add(1, tags);
        console.error(`❌ VU #${vu}: Failed GET: Status ${res.status}`);
    }

    return res;
}


export const teardown = createFindAllByServiceProviderTeardown({
    START_TIME,
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});

export const handleSummary = createHandleSummary({
    START_TIME,
    testName: 'GetAllActivationsByServiceProvider STRESS TEST',
    countTag: 'requestCount',
    reportPrefix: 'findAllByServiceProvider',
    VU_COUNT: VU_COUNT_SET,
    testCompletedRef
});