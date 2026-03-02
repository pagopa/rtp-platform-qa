import http from 'k6/http';
import {
  ActorCredentials,
  buildHeaders,
  endpoints,
  randomFiscalCode,
  setupAuth
} from "../utils/utils.js";

const DEBTOR_SERVICE_PROVIDER_ID_MOCK = __ENV.DEBTOR_SERVICE_PROVIDER_ID_MOCK;
const DEBTOR_SERVICE_PROVIDER_ID_FAKE = __ENV.DEBTOR_SERVICE_PROVIDER_ID_FAKE;

const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 1000;
const FILE_PATH = 'json-file/rtp-activator/activation-otps.json';

let otps = [];

export const options = {
  vus: 1,
  iterations: TARGET_REQUESTS,
  setupTimeout: "30m",
};

export function setup() {
  const DEBTOR_TOKEN_MOCK = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
  const DEBTOR_TOKEN_FAKE = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);

  return { DEBTOR_TOKEN_MOCK, DEBTOR_TOKEN_FAKE };
}

export default function createActivationOtp(data) {
  const { DEBTOR_TOKEN_MOCK, DEBTOR_TOKEN_FAKE } = data;

  let headers = { ...buildHeaders(DEBTOR_TOKEN_FAKE), 'Content-Type': 'application/json' };
  const fiscalCode = randomFiscalCode();

  let payload = {
    payer: { fiscalCode, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID_FAKE }
  };

  const url = endpoints.activations;
  let res = http.post(url, JSON.stringify(payload), { headers });

  if (res.status !== 201) return;

  headers = { ...buildHeaders(DEBTOR_TOKEN_MOCK), 'Content-Type': 'application/json' };
  payload = {
    payer: { fiscalCode, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID_MOCK }
  };

  res = http.post(url, JSON.stringify(payload), { headers });

  if (res.status === 409) {
    const location = res.headers['Location'] || res.headers['location'];
    if (!location) {
      console.warn('409 without Location header');
      return;
    }
    const otp = location.split('/').pop();
    otps.push(otp);
  }
}

export function handleSummary(summaryData) {
  console.log(`💾 Saving ${otps.length} OTPs to file: ${FILE_PATH}`);
  return {
    [FILE_PATH]: JSON.stringify(otps, null, 2),
  };
}