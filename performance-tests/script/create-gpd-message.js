import http from 'k6/http';
import { check } from 'k6';
import {
  ActorCredentials,
  buildHeaders, endpoints,
  randomFiscalCode,
  setupAuth
} from "../utils/utils.js";
import {createGpdMessageInBatch} from "../utils/batch-utils.js";

/**
 * @file GPD Message Creator – Batch setup (k6)
 * @description
 * Activates a randomly generated debtor fiscal code, then generates GPD messages
 * for that debtor in batches during the k6 `setup()` phase and persists only the
 * resulting `operationId`s to a JSON file via `handleSummary()`.
 *
 * GPD messages are always created with operation `CREATE`, status `VALID` and
 * EC tax code `77777777777`.
 *
 * ## Inputs
 * Environment variables:
 * - `DEBTOR_SERVICE_PROVIDER_ID` (required): Service Provider ID used as `rtpSpId` in the activation.
 * - `PSP_TAX_CODE` (optional): PSP tax code.
 * - `TARGET_REQUESTS` (number, optional, default: 10000): Total messages to create.
 * - `BATCH_SIZE` (number, optional, default: 1000): Requests per batch.
 * - `DELAY_BETWEEN_BATCHES` (number, seconds, optional, default: 1): Delay between batches.
 *
 * ## Outputs
 * - JSON file: `json-file/rtp-sender/gpd-message-id.json`
 *   containing generated `operationId`s.
 */

/** Debtor Service Provider ID used for the activation (env: DEBTOR_SERVICE_PROVIDER_ID). @type {string} */
const DEBTOR_SERVICE_PROVIDER_ID = String(__ENV.DEBTOR_SERVICE_PROVIDER_ID);

/** PSP tax code (env: PSP_TAX_CODE). @type {string|null} */
const PSP_TAX_CODE = __ENV.PSP_TAX_CODE || null;

/** Total messages to generate (env: TARGET_REQUESTS, default: 10000). @type {number} */
const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 10000;

/** Requests per batch (env: BATCH_SIZE, default: 1000). @type {number} */
const BATCH_SIZE = Number(__ENV.BATCH_SIZE) || 1000;

/** Delay in seconds between batches (env: DELAY_BETWEEN_BATCHES, default: 1). @type {number} */
const DELAY_BETWEEN_BATCHES = Number(__ENV.DELAY_BETWEEN_BATCHES) || 1;

/** Output file path for generated operation IDs. @type {string} */
const FILE_PATH = 'json-file/rtp-sender/gpd-message-id.json';

/**
 * k6 test options.
 * Extends setup timeout to allow large batch executions.
 *
 * @type {{ setupTimeout: string }}
 */
export const options = {
  setupTimeout: '120m',
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as debtor service provider and activates a random fiscal code
 * (expects HTTP 201). Then authenticates as RTP consumer and creates GPD
 * messages for that fiscal code in batches using `createGpdMessageInBatch`.
 * The resulting operation IDs are returned and passed to `handleSummary()`
 * as `setup_data`.
 *
 * @returns {string[]} List of successfully created operation IDs.
 */
export function setup(){

  const activationAuth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
  const activationHeaders = buildHeaders(activationAuth.access_token);

  const fiscalCode = randomFiscalCode();

  const payload = {
    payer: {
      fiscalCode: fiscalCode,
      rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const url = endpoints.activations;
  const activationRes = http.post(url, JSON.stringify(payload), { headers: activationHeaders });
  check(activationRes, { 'activation 201': r => r.status === 201 });

  if (activationRes.status !== 201) {
    throw new Error(`❌ Failed to create activation for ${fiscalCode}. Status: ${activationRes.status}`);
  }

  const auth = setupAuth(ActorCredentials.RTP_CONSUMER);
  const accessToken = auth.access_token;

  return createGpdMessageInBatch({
    accessToken: accessToken,
    targetRequests: TARGET_REQUESTS,
    batchSize: BATCH_SIZE,
    delayBetweenBatches: DELAY_BETWEEN_BATCHES,
    debtorFiscalCode: fiscalCode,
    operation: "CREATE",
    status: "VALID",
    ecTaxCode: "77777777777",
    psp_tax_code: PSP_TAX_CODE
  });
}

/**
 * Default k6 test function.
 * Not used because all logic runs in `setup()`.
 */
export default function createGpdMessage() {
  // intentionally empty
}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Persists generated operation IDs to a JSON file.
 *
 * @param {{ setup_data?: string[] }} data Setup output.
 * @returns {Record<string, string>} Map of output file paths to serialized contents.
 */
export function handleSummary(data) {
  const idsOnly = (data.setup_data || [])
  .filter(Boolean);

  console.log(`💾 Saving ${idsOnly.length} operationIds to file: ${FILE_PATH}`);

  return {
    [FILE_PATH]: JSON.stringify(idsOnly, null, 2),
  };
}
