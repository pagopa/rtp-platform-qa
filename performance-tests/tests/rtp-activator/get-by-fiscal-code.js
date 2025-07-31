import http from 'k6/http';
import { check, sleep } from 'k6';
import {setupAuth, buildHeaders, endpoints, determineStage, stages, getOptions, randomFiscalCode} from '../../utils/utils.js';
import { Counter, Trend } from 'k6/metrics';

const START_TIME = Date.now();
const {
    DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;

const currentRPS = new Counter('current_rps');
const failureCounter = new Counter('failures');
const successCounter = new Counter('successes');
const responseTimeTrend = new Trend('response_time');

export let options = {
    ...getOptions(__ENV.SCENARIO, 'getByFiscalCode'),
    setupTimeout: '120s'
};

export function setup() {
    const { access_token } = setupAuth();
    const headers = buildHeaders(access_token);
    const fiscalCodes = [];

    console.log('Starting user activation...');
    for (let i = 0; i < 100; i++) {
        const fiscalCode = randomFiscalCode();
        const payload = {
            payer: {
                fiscalCode,
                rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
            }
        };

        const res = http.post(endpoints.activations, JSON.stringify(payload), { headers });

        if (res.status === 201) {
            fiscalCodes.push(fiscalCode);
        } else {
            console.warn(`Activation Error: ${res.status}`);
        }

        sleep(0.1);
    }

    console.log(`Activations completed: ${fiscalCodes.length}`);
    console.log('Waiting 1 minute for it to cool down...');
    sleep(60);

    return { access_token, fiscalCodes };
}

export function getByFiscalCode(data) {
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    const tags = {
        timeWindow: Math.floor(elapsedSeconds / 10) * 10,
        stage: determineStage(elapsedSeconds)
    };

    currentRPS.add(1, tags);

    const fiscalCode = data.fiscalCodes[Math.floor(Math.random() * data.fiscalCodes.length)];
    const headers = buildHeaders(data.access_token);
    headers['PayerId'] = fiscalCode;

    const url = endpoints.getByFiscalCode;

    const start = Date.now();
    const res = http.get(url, { headers });
    const duration = Date.now() - start;

    responseTimeTrend.add(duration, tags);

    if (res.status === 200) {
        successCounter.add(1, tags);
    } else {
        failureCounter.add(1, tags);
    }

    check(res, {
        'get: status is 200': (r) => r.status === 200
    });

    sleep(Math.random() * 2 + 0.5);
    return res;
}

export function handleSummary(data) {
    console.log('Generating enhanced summary...');

    const stageAnalysis = {};

    for (const stage of stages) {
        const stageData = {
            requests: 0,
            successes: 0,
            failures: 0,
            responseTime: {}
        };

        const successValues = Object.values(data.metrics.successes?.values || {});
        if (data.metrics.successes?.values) {
            for (const value of successValues) {
                if (value.tags?.stage === stage) {
                    stageData.successes += value.count;
                    stageData.requests += value.count;
                }
            }
        }

        const failureValues = Object.values(data.metrics.failures?.values || {});
        if (data.metrics.failures?.values) {
            for (const value of failureValues) {
                if (value.tags?.stage === stage) {
                    stageData.failures += value.count;
                    stageData.requests += value.count;
                }
            }
        }

        if (stageData.requests > 0) {
            stageData.successRate = (stageData.successes / stageData.requests) * 100;
            stageData.failureRate = (stageData.failures / stageData.requests) * 100;
        }

        stageAnalysis[stage] = stageData;
    }

    let breakingPoint = null;
    for (const stage of stages) {
        const stageData = stageAnalysis[stage];
        if (stageData?.failureRate > 10) {
            breakingPoint = {
                stage: stage,
                failureRate: stageData.failureRate,
                requests: stageData.requests
            };
            break;
        }
    }

    let firstFailureRPS = null;
    if (data.metrics.failures?.values?.length) {
        const failuresByWindow = data.metrics.failures.values
            .filter(v => v.tags && v.count > 0)
            .sort((a, b) => a.tags.timeWindow - b.tags.timeWindow);

        if (failuresByWindow.length) {
            const first = failuresByWindow[0];
            firstFailureRPS = (first.count / 10) * 60;
        }
    }

    return {
        'stdout': JSON.stringify(data, null, 2),
        'breaking-point-analysis.json': JSON.stringify({
            summary: {
                totalRequests: data.metrics.iterations?.count,
                successRate: data.metrics.checks?.passes / data.metrics.checks?.count,
                failureRate: data.metrics.checks?.fails / data.metrics.checks?.count,
                firstFailureRPS
            },
            breakingPoint,
            stageAnalysis,
            metrics: Object.fromEntries(
                Object.entries(data.metrics).map(([k, v]) => [k, {
                    avg: v.values?.avg,
                    p95: v.values?.['p(95)'],
                    count: v.values?.count
                }])
            )
        }, null, 2)
    };
}