import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { getValidAccessToken } from './utility.js';
import { Counter, Trend } from 'k6/metrics';

const START_TIME = Date.now();

const {
  DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
  DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET,
  DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;

const config = {
  access_token_url: 'https://api-mcshared.uat.cstar.pagopa.it/auth/token',
  activation_base: 'https://api-rtp.uat.cstar.pagopa.it/rtp/activation'
};

const currentRPS = new Counter('current_rps');
const failureCounter = new Counter('failures');
const successCounter = new Counter('successes');
const responseTimeTrend = new Trend('response_time');

export let options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 6000,
      exec: 'activate',
      stages: [
        { target: 50, duration: '30s' },
        { target: 50, duration: '30s' },

        { target: 100, duration: '30s' },
        { target: 100, duration: '30s' },
        
        { target: 250, duration: '30s' },
        { target: 250, duration: '30s' },
        
        { target: 500, duration: '30s' },
        { target: 500, duration: '30s' },
        
        { target: 1000, duration: '30s' },
        { target: 1000, duration: '30s' },
        
        { target: 2500, duration: '30s' },
        { target: 2500, duration: '30s' },
        
        { target: 5000, duration: '30s' },
        { target: 5000, duration: '60s' },
        
        { target: 1000, duration: '30s' },
        { target: 250, duration: '30s' },
        { target: 50, duration: '30s' }
      ]
    },
    soak_test: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 200,
      exec: 'activate'
    },
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 500,
      exec: 'activate',
      stages: [
        { target: 10, duration: '10s' },
        { target: 300, duration: '10s' },
        { target: 300, duration: '30s' },
        { target: 10, duration: '10s' }
      ]
    }
  },
  thresholds: {
    'http_req_duration': ['p(95)<5000'],
    'failures': [],
    'successes': [],
    'current_rps': ['rate>0'],
    'checks': []
  },
  summaryTrendStats: ['avg','min','med','max','p(90)','p(95)','p(99)'],
  systemTags: ['status','method','url','name','group','check','error','scenario']
};

export function setup() {
  if (!DEBTOR_SERVICE_PROVIDER_CLIENT_ID || !DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET) {
    console.error('⚠️ Missing env DEBTOR_SERVICE_PROVIDER_CLIENT_ID or _SECRET');
    throw new Error('Client credentials are not set');
  }
  const token = getValidAccessToken(
    config.access_token_url,
    DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
    DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET
  );
  return { access_token: token };
}

export function activate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const headers = {
    'Authorization': `Bearer ${data.access_token}`,
    'Content-Type': 'application/json',
    'Version': 'v1',
    'RequestId': uuidv4()
  };

  const debtor_fc = Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
  const payload = { payer: { fiscalCode: debtor_fc, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID } };
  const url = `${config.activation_base}/activations?toPublish=true`;

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
    'activation: status is 201': (r) => r.status === 201,
    'activation: valid payload': (r) => r.json('id') !== undefined
  });

  sleep(Math.random() * 2 + 0.5);
  return res;
}

function determineStage(sec) {
  if (sec <= 30) return 'ramp-50';
  if (sec <= 60) return 'stable-50';
  if (sec <= 90) return 'ramp-100';
  if (sec <= 120) return 'stable-100';
  if (sec <= 150) return 'ramp-250';
  if (sec <= 180) return 'stable-250';
  if (sec <= 210) return 'ramp-500';
  if (sec <= 240) return 'stable-500';
  if (sec <= 270) return 'ramp-1000';
  if (sec <= 300) return 'stable-1000';
  if (sec <= 330) return 'ramp-2500';
  if (sec <= 360) return 'stable-2500';
  if (sec <= 390) return 'ramp-5000';
  if (sec <= 450) return 'stable-5000';
  if (sec <= 480) return 'recovery-1000';
  if (sec <= 510) return 'recovery-250';
  return 'recovery-50';
}

export function handleSummary(data) {
  console.log('Generating enhanced summary...');
  
  const stageAnalysis = {};
  const stages = ['ramp-50', 'stable-50', 'ramp-100', 'stable-100', 'ramp-250', 'stable-250', 
                 'ramp-500', 'stable-500', 'ramp-1000', 'stable-1000', 'ramp-2500', 'stable-2500', 
                 'ramp-5000', 'stable-5000', 'recovery-1000', 'recovery-250', 'recovery-50'];
  
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
  
  return {
    'stdout': JSON.stringify(data, null, 2),
    'breaking-point-analysis.json': JSON.stringify({
      summary: {
        totalRequests: data.metrics.iterations.count,
        successRate: data.metrics.checks.passes / data.metrics.checks.count,
        failureRate: data.metrics.checks.fails / data.metrics.checks.count
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
