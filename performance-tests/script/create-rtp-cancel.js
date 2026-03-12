import {ActorCredentials, setupAuth} from "../utils/utils.js";
import {cancelRtpInBatch, sendRtpInBatch} from "../utils/batch-utils.js";

/**
 * @file RTP Sender Cancel – Batch setup (k6)
 * @description
 * Generates RTP requests in batches and immediately cancels them during the k6 `setup()` phase.
 * The resulting cancelled `resourceId`s are persisted to a JSON file via `handleSummary()`.
 *
 * ## Inputs
 * Environment variables:
 * - `DEBTOR_FISCAL_CODE` (required): Fiscal code used in RTP payloads.
 * - `TARGET_REQUESTS` (number, optional, default: 10000): Total RTPs to generate.
 * - `BATCH_SIZE` (number, optional, default: 1000): Requests per batch.
 * - `DELAY_BETWEEN_BATCHES` (number, seconds, optional, default: 1): Delay between batches.
 *
 * ## Outputs
 * - JSON file: `json-file/rtp-sender/resourceIds-cancel.json`
 *   containing cancelled RTP `resourceId`s.
 */

/** Debtor fiscal code from `DEBTOR_FISCAL_CODE` env variable. @type {string} */
const DEBTOR_FISCAL_CODE = String(__ENV.DEBTOR_FISCAL_CODE);

/** Total RTP requests to generate (`TARGET_REQUESTS`, default: 10000). @type {number} */
const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 10000;

/** Requests per batch (`BATCH_SIZE`, default: 1000). @type {number} */
const BATCH_SIZE = Number(__ENV.BATCH_SIZE) || 1000;

/** Delay in seconds between batches (`DELAY_BETWEEN_BATCHES`, default: 1). @type {number} */
const DELAY_BETWEEN_BATCHES = Number(__ENV.DELAY_BETWEEN_BATCHES) || 1;

/** Cached OAuth access token. @type {string|null} */
let token = null;

/** Timestamp when the token was created (ms). @type {number} */
let tokenCreatedAt = 0;

/** Token TTL in milliseconds (4 minutes). @type {number} */
const TOKEN_TTL = 4 * 60 * 1000;

/** Output file path for cancelled RTP resource IDs. @type {string} */
const FILE_PATH = 'json-file/rtp-sender/resourceIds-cancel.json';

/**
 * k6 test options.
 * Extends the setup timeout to allow large batch executions.
 *
 * @type {{ setupTimeout: string }}
 */
export const options = {
  setupTimeout: '60m',
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as a Creditor Service Provider, generates RTP requests in batches,
 * and immediately cancels them using `cancelRtpInBatch`.
 * The cancelled resource IDs are returned and passed to `handleSummary()` as `setup_data`.
 *
 * @returns {Array<{ id: string, payerId?: string }>} List of successfully cancelled RTP requests.
 */
export function setup() {

  if (!token || (Date.now() - tokenCreatedAt) > TOKEN_TTL) {
    const auth = setupAuth(ActorCredentials.CREDITOR_SERVICE_PROVIDER);
    token = auth.access_token;
    tokenCreatedAt = Date.now();
    console.log(`🔄 VU ${__VU} refreshed token`);
  }

  const resourceIds = sendRtpInBatch({
    accessToken: token,
    targetRequests: TARGET_REQUESTS,
    batchSize: BATCH_SIZE,
    delayBetweenBatches: DELAY_BETWEEN_BATCHES,
    debtorFiscalCode: DEBTOR_FISCAL_CODE,
  });

  return cancelRtpInBatch({
    accessToken: token,
    resourceIds: resourceIds,
    batchSize: BATCH_SIZE,
    delayBetweenBatches: DELAY_BETWEEN_BATCHES,
  });
}

/**
 * Default k6 test function.
 * Not used because all logic runs in `setup()`.
 */
export default function createRtpCancel () {
  // intentionally empty
}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Extracts RTP resource identifiers from `setup_data`
 * and writes them to a JSON file for later usage.
 *
 * @param {{ setup_data?: Array<{ id?: string, resourceId?: string }> }} data
 * Object containing the output returned by `setup()`.
 *
 * @returns {Record<string, string>} Map of output file paths to serialized contents.
 */
export function handleSummary(data) {
  const idsOnly = (data.setup_data || [])
  .map((r) => r?.id || r.resourceId)
  .filter(Boolean);

  console.log(`💾 Saving ${idsOnly.length} resourceIds to file: ${FILE_PATH}`);

  return {
    [FILE_PATH]: JSON.stringify(idsOnly, null, 2),
  };
}