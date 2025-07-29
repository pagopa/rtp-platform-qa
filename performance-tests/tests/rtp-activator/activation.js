import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { setupAuth, randomFiscalCode, config as activationConfig } from '../../utils/activation_utils.js';

const {
  DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;


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
  return setupAuth();
}

export function activate(data) {
  const headers = {
    'Authorization': `Bearer ${data.access_token}`,
    'Content-Type':  'application/json',
    'Version':       'v1',
    'RequestId':     uuidv4()
  };

  const debtor_fc = randomFiscalCode();
  const payload = {
    payer: {
      fiscalCode: debtor_fc,
      rtpSpId:    DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const url = `${activationConfig.activation_base}/activations?toPublish=true`;
  const res = http.post(url, JSON.stringify(payload), { headers });
  check(res, { 'activation 201': r => r.status === 201 });
  
  sleep(1);
  return res;
}