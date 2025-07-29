import { getValidAccessToken } from './utility.js';
import { activationConfig } from '../config/config.js';

export const config = activationConfig;
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export function setupAuth() {
    const { DEBTOR_SERVICE_PROVIDER_CLIENT_ID, DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET } = __ENV;
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

export function randomFiscalCode() {
    return Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
}
export const commonOptions = {
  summaryTrendStats: ['avg','min','med','max','p(90)','p(95)','p(99)'],
  systemTags: ['status','method','url','name','group','check','error','scenario'],
};

export const progressiveOptions = {
  ...commonOptions,
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
    http_req_duration: ['p(95)<5000'],
    failures: [],
    successes: [],
    current_rps: ['rate>0'],
    checks: []
  }
};

progressiveOptions.scenarios.stress_test_fixed_user = {
  executor: 'constant-vus',
  vus: progressiveOptions.scenarios.stress_test.maxVUs,
  duration: '9m',
  exec: 'activate'
};
progressiveOptions.scenarios.soak_test_fixed_user = {
  executor: 'constant-vus',
  vus: progressiveOptions.scenarios.soak_test.maxVUs,
  duration: progressiveOptions.scenarios.soak_test.duration,
  exec: 'activate'
};
progressiveOptions.scenarios.spike_test_fixed_user = {
  executor: 'constant-vus',
  vus: progressiveOptions.scenarios.spike_test.maxVUs,
  duration: '1m',
  exec: 'activate'
};

export function buildHeaders(token) {
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'Version': 'v1',
    'RequestId': uuidv4()
  };
}

export function determineStage(sec) {
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

export const stages = [
  'ramp-50', 'stable-50', 'ramp-100', 'stable-100', 'ramp-250', 'stable-250',
  'ramp-500', 'stable-500', 'ramp-1000', 'stable-1000', 'ramp-2500', 'stable-2500',
  'ramp-5000', 'stable-5000', 'recovery-1000', 'recovery-250', 'recovery-50'
];

export const endpoints = {
  activations: `${activationConfig.activation_base}/activations?toPublish=true`
};

export function getOptions(scenarioName) {
  const scenarioKey = scenarioName in progressiveOptions.scenarios
    ? scenarioName
    : 'stress_test';
  return {
    summaryTrendStats: progressiveOptions.summaryTrendStats,
    systemTags: progressiveOptions.systemTags,
    scenarios: {
      [scenarioKey]: progressiveOptions.scenarios[scenarioKey]
    },
    thresholds: progressiveOptions.thresholds
  };
}
