import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { getValidAccessToken } from '../../utils/utility.js';

const {
  DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
  DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET,
  DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;

const config = {
  access_token_url: 'https://api-mcshared.uat.cstar.pagopa.it/auth/token',
  activation_base: 'https://api-rtp.uat.cstar.pagopa.it/rtp/activation'
};

export let options = {
  scenarios: {
    load100: {
      executor: 'constant-arrival-rate', 
      rate: 100, 
      timeUnit: '1s', 
      duration: '30s',
      preAllocatedVUs: 100, 
      maxVUs: 200, 
      exec: 'activate',  
      startTime: '0s',
    },
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  systemTags: ['status', 'method', 'url', 'name', 'group', 'check', 'error', 'scenario']
};

export function setup() {
  if (!DEBTOR_SERVICE_PROVIDER_CLIENT_ID || !DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET) {
    console.error(`⚠️ Missing env DEBTOR_SERVICE_PROVIDER_CLIENT_ID or _SECRET`);
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
  const headers = {
    'Authorization': `Bearer ${data.access_token}`,
    'Content-Type':  'application/json',
    'Version':       'v1',
    'RequestId':     uuidv4()
  };

  const debtor_fc = Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
  const payload = {
    payer: {
      fiscalCode: debtor_fc,
      rtpSpId:    DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const url = `${config.activation_base}/activations?toPublish=true`;
  const res = http.post(url, JSON.stringify(payload), { headers });
  check(res, { 'activation 201': r => r.status === 201 });
  
  sleep(1);
  return res;
}