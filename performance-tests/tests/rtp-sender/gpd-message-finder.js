import http from 'k6/http';
import {check, sleep} from 'k6';
import {createStandardMetrics} from "../../utils/metrics-utils.js";
import {
  ActorCredentials,
  buildHeaders,
  determineStage,
  endpoints,
  generatePositiveLong,
  getOptions,
  setupAuth
} from "../../utils/utils.js";
import {buildGpdMessagePayload} from "../../utils/sender-payloads.js";
import {uuidv4} from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

const START_TIME = Date.now();

const VU_COUNT = Number(__ENV.VU_COUNT_SET) || 10;

const ITERATIONS = Number(__ENV.ITERATIONS) || 1000;

const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

const activationFiscalCodes = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activations.json'))
    .map(r => r?.fiscalCode)
    .filter(fc => fc != null && fc !== '')
)).map(String);

const wrappedActivations = activationFiscalCodes.map(
    fiscalCode => ({fiscalCode}));

const {
  currentRPS,
  failureCounter,
  successCounter,
  responseTimeTrend
} = createStandardMetrics();

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export const options = {
  ...getOptions('stress_test_fixed_user', 'sendMessage'),
  setupTimeout: '5m',
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT,
      iterations: ITERATIONS,
      maxDuration: '30m',
      gracefulStop: '30s',
      exec: 'sendMessage'
    }
  }
};

export function setup() {
  const consumerAuth = setupAuth(ActorCredentials.RTP_CONSUMER);

  return {
    consumerToken: consumerAuth.access_token
  }
}

export function sendMessage(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU),
  };

  currentRPS.add(1, tags);

  const headers = {
    ...buildHeaders(data.consumerToken),
    "Idempotency-Key": uuidv4()
  };

  const picked = randomItem(wrappedActivations);
  const fiscalCode = picked?.fiscalCode;

  const payload = buildGpdMessagePayload(fiscalCode,
      generatePositiveLong(), "CREATE", "VALID");

  const start = Date.now();
  const res = http.post(endpoints.gpdMessage, JSON.stringify(payload),
      {headers: headers});
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 200) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    if (Math.random() < 0.1) {
      console.error(
          `❌ VU #${__VU}: Failed send gpd message — Status ${res.status}`);
    }
  }

  check(res, {
    'GpdMessage: status is 200': (r) => r.status === 200
  });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }
}