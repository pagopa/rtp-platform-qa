import { ActorCredentials, setupAuth } from '../utils/utils.js';
import { createDeliveryStatusDataInBatch } from '../utils/batch-utils.js';

/**
 * @file Delivery-Status Data Creator – Batch setup (k6)
 * @description
 * Creates GPD messages in batches during the k6 `setup()` phase.
 * For each successfully sent message, it persists the `noticeNumber` (nav) and
 * `payeeId` (ec_tax_code) into a JSON fixture file via `handleSummary()`.
 *
 * Those pairs are the exact query-parameter inputs required by:
 *   GET /rtps/delivery-status?noticeNumber=<nav>&payeeId=<ec_tax_code>
 *
 * The generated file is consumed by `tests/rtp-sender/delivery-status-finder.js`
 * to drive the delivery-status stress test.
 *
 * ## Inputs — Environment variables
 * | Variable                | Required | Default | Description                             |
 * |-------------------------|----------|---------|-----------------------------------------|
 * | `DEBTOR_FISCAL_CODE`    | ✅       | —       | Fiscal code used in every GPD payload   |
 * | `EC_TAX_CODE`           | ✅       | —       | Creditor entity tax code (= payeeId)    |
 * | `OPERATION`             | ❌       | CREATE  | GPD operation type                      |
 * | `STATUS`                | ❌       | VALID   | GPD message status                      |
 * | `PSP_TAX_CODE`          | ❌       | null    | Optional PSP tax code                   |
 * | `TARGET_REQUESTS`       | ❌       | 10000   | Total GPD messages to send              |
 * | `BATCH_SIZE`            | ❌       | 100     | Requests per batch                      |
 * | `DELAY_BETWEEN_BATCHES` | ❌       | 1       | Delay between batches (seconds)         |
 *
 * ## Output
 * - `json-file/rtp-sender/delivery-status-inputs.json`
 *   Array of `{ noticeNumber: string, payeeId: string }` objects.
 */

/**
 * Reads a required environment variable and throws at init time if it is
 * absent or was coerced to the literal string "undefined" by k6.
 *
 * @param {string} name - Environment variable name.
 * @returns {string} The variable value.
 * @throws {Error} If the variable is not set or equals "undefined".
 */
function requireEnv(name) {
  const value = __ENV[name];
  if (value === undefined || value === null || value === 'undefined' || value.trim() === '') {
    throw new Error(
      `❌ Required environment variable "${name}" is not set.\n` +
      `Make sure it is defined in ../.env or passed explicitly:\n` +
      `  ${name}=<value> ./run-tests.sh script/create-delivery-status.js console`
    );
  }
  return value;
}

/** Debtor fiscal code — required (env: DEBTOR_FISCAL_CODE). @type {string} */
const DEBTOR_FISCAL_CODE = requireEnv('DEBTOR_FISCAL_CODE');

/** Creditor entity tax code, used as payeeId — required (env: EC_TAX_CODE). @type {string} */
const EC_TAX_CODE = requireEnv('EC_TAX_CODE');

/** GPD operation type (env: OPERATION, default: CREATE). @type {string} */
const OPERATION = __ENV.OPERATION || 'CREATE';

/** GPD message status (env: STATUS, default: VALID). @type {string} */
const STATUS = __ENV.STATUS || 'VALID';

/** Optional PSP tax code (env: PSP_TAX_CODE). @type {string|null} */
const PSP_TAX_CODE = __ENV.PSP_TAX_CODE || null;

/** Total messages to generate (env: TARGET_REQUESTS, default: 10000). @type {number} */
const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 10000;

/** Requests per batch (env: BATCH_SIZE, default: 1000). @type {number} */
const BATCH_SIZE = Number(__ENV.BATCH_SIZE) || 1000;

/** Delay in seconds between batches (env: DELAY_BETWEEN_BATCHES, default: 1). @type {number} */
const DELAY_BETWEEN_BATCHES = Number(__ENV.DELAY_BETWEEN_BATCHES) || 1;

/** Output file path for the generated delivery-status inputs. @type {string} */
const FILE_PATH = 'json-file/rtp-sender/delivery-status-inputs.json';


/**
 * k6 test options.
 * Only `setupTimeout` is relevant; all work happens in `setup()`.
 *
 * @type {{ setupTimeout: string }}
 */
export const options = {
  setupTimeout: '120m',
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `RTP_CONSUMER` and calls `createDeliveryStatusDataInBatch`
 * to send GPD messages and collect the resulting noticeNumber/payeeId pairs.
 *
 * @returns {Array<{ noticeNumber: string, payeeId: string }>} Delivery-status inputs collected.
 */
export function setup() {
  const auth = setupAuth(ActorCredentials.RTP_CONSUMER);
  const accessToken = auth.access_token;

  return createDeliveryStatusDataInBatch({
    accessToken,
    targetRequests: TARGET_REQUESTS,
    batchSize: BATCH_SIZE,
    delayBetweenBatches: DELAY_BETWEEN_BATCHES,
    debtorFiscalCode: DEBTOR_FISCAL_CODE,
    operation: OPERATION,
    status: STATUS,
    ecTaxCode: EC_TAX_CODE,
    psp_tax_code: PSP_TAX_CODE,
  });
}

/**
 * Default k6 test function — intentionally empty.
 * All logic runs in `setup()` and `handleSummary()`.
 */
export default function createDeliveryStatus() {
  // intentionally empty: only setup() + handleSummary()
}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Persists the noticeNumber/payeeId pairs produced by `setup()` to a JSON fixture file.
 *
 * @param {{ setup_data?: Array<{ noticeNumber: string, payeeId: string }> }} data
 *   Object containing the output returned by `setup()`.
 *
 * @returns {Record<string, string>} Map of output file paths to serialized JSON contents.
 */
export function handleSummary(data) {
  const inputs = (data.setup_data || []).filter(
    (entry) => entry && entry.noticeNumber && entry.payeeId
  );

  console.log(`Saving ${inputs.length} delivery-status inputs to file: ${FILE_PATH}`);

  return {
    [FILE_PATH]: JSON.stringify(inputs, null, 2),
  };
}
