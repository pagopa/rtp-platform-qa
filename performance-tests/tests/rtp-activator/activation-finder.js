import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, determineStage, stages, getOptions } from '../../utils/utils.js';
import { Counter, Trend } from 'k6/metrics';
import { createHandleSummary } from '../../utils/summary-utils.js';

const START_TIME = Date.now();
const { DEBTOR_SERVICE_PROVIDER_ID } = __ENV;

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


export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'ACTIVATION STRESS TEST',
  countTag: 'activatedCount',
  reportPrefix: 'activation',
  VU_COUNT: 50
});

