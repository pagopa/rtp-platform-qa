import http from 'k6/http';
import { check, sleep } from 'k6';
import {createStandardMetrics} from "../../utils/metrics-utils.js";
import {
  ActorCredentials, buildHeaders,
  determineStage, endpoints,
  getOptions,
  setupAuth
} from "../../utils/utils.js";


const START_TIME = Date.now();

const VU_COUNT_SET = Number(__ENV.VU_COUNT_SET) || 10;

const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

let token = null;
let tokenCreatedAt = 0;

const TOKEN_TTL = 4 * 60 * 1000;

const activationOtps = Array.from(new Set(
    JSON.parse(open('../../json-file/rtp-activator/activation-otps.json'))
)).map(String);


const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export const options = {
  ...getOptions('stress_test_fixed_user', 'takeover'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: activationOtps.length,
      maxDuration: '30m',
      gracefulStop: '30m',
      exec: 'takeover'
    }
  }
};

export function takeover(data){

  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    vu: String(__VU),
  };

  currentRPS.add(1, tags);

  if (!token || (Date.now() - tokenCreatedAt) > TOKEN_TTL) {
    const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
    token = auth.access_token;
    tokenCreatedAt = Date.now();
    console.log(`🔄 VU ${__VU} refreshed token`);
  }

  const otp = activationOtps[__ITER];

  const endpoint = `${endpoints.takeover}/${otp}`
  const headers = { ...buildHeaders(token)};

  const start = Date.now();
  let res = http.post(endpoint, null, {headers});
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 201) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
    console.error(
        `❌ VU #${__VU}: Failed takeover — Status ${res.status}`);
  }

  check(res, {
    'Takeover: status is 201': (r) => r.status === 201
  });

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

}
