import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, determineStage, stages, getOptions } from '../../utils/activation_utils.js';
import { Counter, Trend } from 'k6/metrics';

const START_TIME = Date.now();

const {
  DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;


const currentRPS = new Counter('current_rps');
const failureCounter = new Counter('failures');
const successCounter = new Counter('successes');
const responseTimeTrend = new Trend('response_time');


export let options = getOptions(__ENV.SCENARIO, 'activate');

export function setup() {
  return setupAuth();
}

export function activate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const headers = buildHeaders(data.access_token);

  const debtor_fc = randomFiscalCode();
  const payload = { payer: { fiscalCode: debtor_fc, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID } };
  const url = endpoints.activations;

  const start = Date.now();
  const res = http.post(url, JSON.stringify(payload), { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 201) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
  }

  check(res, {
    'activation: status is 201': (r) => r.status === 201
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
    
    if (data.metrics.successes && data.metrics.successes.values) {
      for (const value of data.metrics.successes.values) {
        if (value.tags && value.tags.stage === stage) {
          stageData.successes += value.count;
          stageData.requests += value.count;
        }
      }
    }
    
    if (data.metrics.failures && data.metrics.failures.values) {
      for (const value of data.metrics.failures.values) {
        if (value.tags && value.tags.stage === stage) {
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
    if (stageData && stageData.requests > 0 && stageData.failureRate > 10) {
      breakingPoint = {
        stage: stage,
        failureRate: stageData.failureRate,
        requests: stageData.requests
      };
      break;
    }
  }

  let firstFailureRPS = null;
  if (data.metrics.failures && data.metrics.failures.values) {
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
        totalRequests: data.metrics.iterations.count,
        successRate: data.metrics.checks.passes / data.metrics.checks.count,
        failureRate: data.metrics.checks.fails / data.metrics.checks.count,
        firstFailureRPS: firstFailureRPS
      },
      breakingPoint: breakingPoint,
      stageAnalysis: stageAnalysis,
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
