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

const REFRESH_EVERY_MS = 15 * 60 * 1000;
const SKEW_MS = 15 * 1000;

let consumerToken = null;
let nextRefreshAt = 0;

function ensureToken() {
  const now = Date.now();

  if (!consumerToken || now >= nextRefreshAt) {
    const auth = setupAuth(ActorCredentials.RTP_CONSUMER);

    consumerToken = auth.access_token;

    if (auth.expires_in) {
      nextRefreshAt = now + (auth.expires_in * 1000) - SKEW_MS;
    } else {
      nextRefreshAt = now + REFRESH_EVERY_MS - SKEW_MS;
    }
  }

  return consumerToken;
}

const activationFiscalCodes = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activations.json'))
    .map(r => r?.fiscalCode)
    .filter(fc => fc != null && fc !== '')
)).map(String);

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
  const wrappedActivations = activationFiscalCodes.map(
      fiscalCode => ({fiscalCode}));
  return {fiscalCodes: wrappedActivations};
}

export function sendMessage(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU),
  };

  currentRPS.add(1, tags);

  const token = ensureToken();

  const headers = {
    ...buildHeaders(token),
    "Idempotency-Key": uuidv4()
  };

  const picked = randomItem(data.fiscalCodes);
  const fiscalCode = picked?.fiscalCode;

  const payload = buildGpdMessagePayload(
      fiscalCode,
      generatePositiveLong(),
      "CREATE",
      "VALID"
  );

  const start = Date.now();
  let res = http.post(endpoints.gpdMessage, JSON.stringify(payload), {headers});
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 200) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(
        `❌ VU #${__VU}: Failed send gpd message — Status ${res.status}`);
  }

  check(res, {
    'GpdMessage: status is 200': (r) => r.status === 200
  });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }
}