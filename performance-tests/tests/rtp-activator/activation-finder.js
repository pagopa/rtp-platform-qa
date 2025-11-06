import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, determineStage, getOptions, ActorCredentials } from '../../utils/utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationTeardown } from '../../utils/teardown-utils.js';

// === CONFIG ===
const START_TIME = Date.now();
const DEBTOR_SERVICE_PROVIDER_ID = String(__ENV.DEBTOR_SERVICE_PROVIDER_ID);
const VU_COUNT = Number(__ENV.VU_COUNT_SET) || 10;
const ITERATIONS = Number(__ENV.ITERATIONS) || 30000;
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

if (!__ENV.DEBTOR_SERVICE_PROVIDER_ID) {
    throw new Error("❌ DEBTOR_SERVICE_PROVIDER_ID cannot be null or undefined");
}

// === METRICS ===
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

// === TEST STATE REFERENCE ===
const testCompletedRef = { value: false };

// === K6 OPTIONS ===
export let options = {
  ...getOptions('stress_test_fixed_user', 'activate'),
  setupTimeout: '5m',
    scenarios: {
        stress_test_fixed_user: {
            executor: 'shared-iterations',
            vus: VU_COUNT,
            iterations: ITERATIONS,
            maxDuration: '30m',
            gracefulStop: '30m',
            exec: 'activate'
        }
    }
};

// === SETUP ===
export function setup() {
  return setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
}

// === MAIN TEST FUNCTION ===
export function activate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const headers = { ...buildHeaders(data.access_token), 'Content-Type': 'application/json' };
  const debtorFiscalCode = randomFiscalCode();

  const payload = {
    payer: {
      fiscalCode: debtorFiscalCode,
      rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const url = endpoints.activations;

  const start = Date.now();
  const res = http.post(url, JSON.stringify(payload), { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 201) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Activation failed — Status ${res.status}, Body: ${res.body}`);
  }

  check(res, {
    'activation: status is 201': (r) => r.status === 201
  });

    if (SLEEP_ITER > 0) {
        sleep(SLEEP_ITER);
    }

  return res;
}

// === TEARDOWN ===
export const teardown = createActivationTeardown({
  START_TIME,
  VU_COUNT,
  testCompletedRef
});

// === SUMMARY ===
export const handleSummary = (opts) => {
    testCompletedRef.value = true;
    return createHandleSummary({
        START_TIME,
        testName: 'ACTIVATION STRESS TEST',
        countTag: 'requestCount',
        reportPrefix: 'activation',
        VU_COUNT,
        testCompletedRef
    })(opts);
};
