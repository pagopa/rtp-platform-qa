import http from 'k6/http';
import {
  ActorCredentials,
  buildHeaders,
  endpoints,
  randomFiscalCode,
  setupAuth
} from "../utils/utils.js";

const DEBTOR_SERVICE_PROVIDER_ID_FAKE = __ENV.DEBTOR_SERVICE_PROVIDER_ID_FAKE;
const DEBTOR_SERVICE_PROVIDER_ID_MOCK = __ENV.DEBTOR_SERVICE_PROVIDER_ID_MOCK;

const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 1000;
const FILE_PATH = 'json-file/rtp-activator/activation-otps.json';

let fakeSpToken = null;
let fakeSpTokenCreatedAt = 0;

let mockSpToken = null;
let mockSpTokenCreatedAt = 0;

const TOKEN_TTL = 4 * 60 * 1000;

let otps = [];

export const options = {
  setupTimeout: "30m",
};

export function setup(){

  if (!fakeSpToken || (Date.now() - fakeSpTokenCreatedAt) > TOKEN_TTL) {
    const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER_FAKESP);
    fakeSpToken = auth.access_token;
    fakeSpTokenCreatedAt = Date.now();
    console.log(`🔄 VU ${__VU} refreshed token`);
  }

  if (!mockSpToken || (Date.now() - mockSpTokenCreatedAt) > TOKEN_TTL) {
    const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
    mockSpToken = auth.access_token;
    mockSpTokenCreatedAt = Date.now();
    console.log(`🔄 VU ${__VU} refreshed token`);
  }

  const url = endpoints.activations;
  const otps = [];

  for (let i = 0; i < TARGET_REQUESTS; i++) {

    const fiscalCode = randomFiscalCode();
    let headers = { ...buildHeaders(fakeSpToken)};
    let payload = { payer: {fiscalCode, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID_FAKE}};
    let res = http.post(url, JSON.stringify(payload), { headers });

    if (res.status === 201){
      headers = { ...buildHeaders(mockSpToken)};
      payload = { payer: {fiscalCode, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID_MOCK}};
      res = http.post(url, JSON.stringify(payload), {headers});

      if (res.status === 409) {
        const location = res.headers['Location'] || res.headers['location'];
        if (!location) {
          console.warn(`409 without location. Body: ${res.body}`);
          return;
        }
        const otp = location.split('/').pop();
        otps.push(otp);
      }
      else {
        console.error(`Second call: expected 409, got ${res.status}`);
      }

    }
    else {
      console.error(`First call: expected 201, got ${res.status}`);
    }
  }

  console.log(`✅ Generated OTPs: ${otps.length}/${TARGET_REQUESTS}`);
  return otps;
}

export default function () {}

export function handleSummary(data) {
  const otps = data.setup_data || [];
  console.log(`💾 Saving ${otps.length} OTPs to file: ${FILE_PATH}`);
  return { [FILE_PATH]: JSON.stringify(otps, null, 2) };
}