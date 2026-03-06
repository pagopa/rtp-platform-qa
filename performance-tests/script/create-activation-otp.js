import http from 'k6/http';
import {
  ActorCredentials,
  buildHeaders,
  endpoints,
  randomFiscalCode,
  setupAuth
} from "../utils/utils.js";

/**
 * @file RTP Activator - Activation OTP Generator (k6 script)
 *
 * @description
 * Generates RTP activation OTPs by creating an activation under a *fake* debtor service provider
 * and then re-submitting the same payer fiscal code under a *mock* debtor service provider.
 *
 * The expected API behavior is:
 * 1) POST activation with FAKE SP -> HTTP 201 Created
 * 2) POST activation with MOCK SP (same fiscal code) -> HTTP 409 Conflict
 *    - with a `Location` header containing the OTP reference.
 *
 * OTPs are generated during the k6 `setup()` phase and persisted to a JSON file via
 * `handleSummary()` using `data.setup_data`.
 *
 * ## Environment Variables
 * - `DEBTOR_SERVICE_PROVIDER_ID_FAKE` (required): Service Provider ID for the FAKE SP.
 * - `DEBTOR_SERVICE_PROVIDER_ID_MOCK` (required): Service Provider ID for the MOCK SP.
 * - `TARGET_REQUESTS` (optional, default: 1000): Number of OTPs to attempt to generate.
 *
 * ## Output
 * - File: `json-file/rtp-activator/activation-otps.json`
 * - Format: JSON array of OTP strings (UUIDs)
 */

/** Debtor Service Provider ID for the FAKE provider (from env). */
const DEBTOR_SERVICE_PROVIDER_ID_FAKE = __ENV.DEBTOR_SERVICE_PROVIDER_ID_FAKE;

/** Debtor Service Provider ID for the MOCK provider (from env). */
const DEBTOR_SERVICE_PROVIDER_ID_MOCK = __ENV.DEBTOR_SERVICE_PROVIDER_ID_MOCK;

/** Number of OTPs to attempt to generate. */
const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 1000;

/** Path where generated OTPs will be saved. */
const FILE_PATH = 'json-file/rtp-activator/activation-otps.json';

/** Cached access token for FAKE SP authentication. */
let fakeSpToken = null;

/** Timestamp (ms) when FAKE SP token was created. */
let fakeSpTokenCreatedAt = 0;

/** Cached access token for MOCK SP authentication. */
let mockSpToken = null;

/** Timestamp (ms) when MOCK SP token was created. */
let mockSpTokenCreatedAt = 0;

/** Token time-to-live (4 minutes). */
const TOKEN_TTL = 4 * 60 * 1000;

/**
 * k6 execution options.
 *
 * This script generates data in `setup()`, so no VU iterations are required.
 *
 * @type {{ setupTimeout: string }}
 */
export const options = {
  setupTimeout: "30m",
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as both FAKE SP and MOCK SP, then generates activation OTPs by:
 * - Creating an activation under FAKE SP (expects 201)
 * - Creating another activation with same fiscalCode under MOCK SP (expects 409 + Location)
 *
 * @returns {string[]} List of generated activation OTPs.
 */
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
          console.warn(`409 without location.`);
          continue;
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

/**
 * Default k6 function.
 *
 * Intentionally empty: OTP generation happens entirely during `setup()`.
 */
export default function createActivationOtp () {
// intentionally empty: only setup() + handleSummary()
}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Persists OTPs generated in `setup()` to disk so they can be reused by other tests.
 *
 * @param {{ setup_data?: string[] }} data Object containing `setup_data` returned by `setup()`.
 * @returns {Record<string, string>} Map of output file paths to file contents.
 */
export function handleSummary(data) {
  const otps = data.setup_data || [];
  console.log(`💾 Saving ${otps.length} OTPs to file: ${FILE_PATH}`);
  return { [FILE_PATH]: JSON.stringify(otps, null, 2) };
}
