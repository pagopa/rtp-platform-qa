import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { setupAuth, randomFiscalCode, activationConfig, commonOptions, buildHeaders, endpoints } from '../../utils/activation_utils.js';

const {
  DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;


export let options = {
  ...commonOptions,
  scenarios: {
    activate: {
      executor: 'constant-arrival-rate',
      rate: 10, timeUnit: '1s', duration: '1m',
      preAllocatedVUs: 10, maxVUs: 50,
      exec: 'activate'
    }
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks:          ['rate>0.95']
  }
};

export function setup() {
  const { access_token } = setupAuth();
  const activationIds = [];
  const headers = buildHeaders(access_token);
  for (let i = 0; i < 20; i++) {
    const fc = randomFiscalCode();
    const res = http.post(
      endpoints.activations,
      JSON.stringify({ payer: { fiscalCode: fc, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID } }),
      { headers }
    );
    if (res.status === 201) {
      activationIds.push(res.headers['Location'].split('/').pop());
    }
  }
  return { access_token, activationIds };
}

export function activate(data) {
  const headers = {
    'Authorization': `Bearer ${data.access_token}`,
    'Content-Type':  'application/json',
    'Version':       'v1',
    'RequestId':     uuidv4(),
  };

  const debtor_fc = Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
  const activationPayload = {
    payer: {
      fiscalCode: debtor_fc,
      rtpSpId:   DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  console.log('> payload for activation:', JSON.stringify(activationPayload));
  const actRes = http.post(
    `${activationConfig.activation_base}/activations?toPublish=true`,
    JSON.stringify(activationPayload),
    { headers }
  );
  console.log(`> POST /activations?toPublish=true → status=${actRes.status}, body=${actRes.body}`);
  check(actRes, { 'activation 201': r => r.status === 201 });

  if (actRes.status === 201) {
    const activationId = actRes.headers['Location'].split('/').pop();

    const getByIdRes = http.get(
    `${activationConfig.activation_base}/activations/${activationId}`,
      { headers }
    );
    console.log(`> GET /activations/${activationId} → status=${getByIdRes.status}`);
    check(getByIdRes, { 'get by id 200': r => r.status === 200 });

    const deactRes = http.del(
    `${activationConfig.activation_base}/activations/${activationId}`,
      null,
      { headers }
    );
    console.log(`> DELETE /activations/${activationId} → status=${deactRes.status}`);
    check(deactRes, { 'deactivation 204': r => r.status === 204 });
  }

  sleep(1);
}