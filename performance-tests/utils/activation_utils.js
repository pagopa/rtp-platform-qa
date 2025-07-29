import { getValidAccessToken } from './utility.js';
import { activationConfig } from '../config/config.js';

export const config = activationConfig;

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
