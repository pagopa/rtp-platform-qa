import http from 'k6/http';
import { check } from 'k6';
import {
  ActorCredentials,
  buildHeaders,
  endpoints,
  randomFiscalCode,
  setupAuth,
  TEST_EC_TAX_CODE
} from '../utils/utils.js';
import { createDeliveryStatusDataInBatch } from '../utils/batch-utils.js';

/**
 * @file Delivery-Status Data Creator – Batch setup (k6)
 * @description
 * Creates GPD messages in batches during the k6 `setup()` phase.
 * If DEBTOR_FISCAL_CODE is not provided, generates a random debtor fiscal code
 * and activates it first (matching create-gpd-message.js).
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
 * | `DEBTOR_SERVICE_PROVIDER_ID` | ❌   | —       | SP ID for activation (if auto-generated)|
 * | `DEBTOR_FISCAL_CODE`    | ❌       | random  | Optional fiscal code override           |
 * | `EC_TAX_CODE`           | ❌       | 77777777777 | Creditor entity tax code (= payeeId)|
 * | `OPERATION`             | ❌       | CREATE  | GPD operation type                      |
 * | `STATUS`                | ❌       | VALID   | GPD message status                      |
 * | `PSP_TAX_CODE`          | ❌       | null    | Optional PSP tax code                   |
 * | `TARGET_REQUESTS`       | ❌       | 10000   | Total GPD messages to send              |
 * | `BATCH_SIZE`            | ❌       | 1000    | Requests per batch                      |
 * | `DELAY_BETWEEN_BATCHES` | ❌       | 1       | Delay between batches (seconds)         |
 *
 * ## Output
 * - `json-file/rtp-sender/delivery-status-inputs.json`
 *   Array of `{ noticeNumber: string, payeeId: string }` objects.
 */

/** Debtor Service Provider ID used for the activation if fiscal code is generated. */
const DEBTOR_SERVICE_PROVIDER_ID = __ENV.DEBTOR_SERVICE_PROVIDER_ID;

/** Creditor entity tax code, used as payeeId (env: EC_TAX_CODE, default: TEST_EC_TAX_CODE). */
const EC_TAX_CODE = __ENV.EC_TAX_CODE || TEST_EC_TAX_CODE;

/** GPD operation type (env: OPERATION, default: CREATE). */
const OPERATION = __ENV.OPERATION || 'CREATE';

/** GPD message status (env: STATUS, default: VALID). */
const STATUS = __ENV.STATUS || 'VALID';

/** Optional PSP tax code (env: PSP_TAX_CODE). */
const PSP_TAX_CODE = __ENV.PSP_TAX_CODE || null;

/** Total messages to generate (env: TARGET_REQUESTS, default: 10000). */
const TARGET_REQUESTS = Number(__ENV.TARGET_REQUESTS) || 10000;

/** Requests per batch (env: BATCH_SIZE, default: 1000). */
const BATCH_SIZE = Number(__ENV.BATCH_SIZE) || 1000;

/** Delay in seconds between batches (env: DELAY_BETWEEN_BATCHES, default: 1). */
const DELAY_BETWEEN_BATCHES = Number(__ENV.DELAY_BETWEEN_BATCHES) || 1;

/** Output file path for the generated delivery-status inputs. */
const FILE_PATH = 'json-file/rtp-sender/delivery-status-inputs.json';

/**
 * k6 test options.
 * Only `setupTimeout` is relevant; all work happens in `setup()`.
 */
export const options = {
  setupTimeout: '120m',
};

/**
 * k6 `setup()` lifecycle function.
 *
 * Resolves or generates/activates a debtor fiscal code, then authenticates as
 * `RTP_CONSUMER` and calls `createDeliveryStatusDataInBatch` to generate
 * messages and collect noticeNumber/payeeId pairs.
 */
export function setup() {
  let fiscalCode = __ENV.DEBTOR_FISCAL_CODE;

  if (!fiscalCode || fiscalCode.trim() === '' || fiscalCode === 'undefined') {
    fiscalCode = randomFiscalCode();

    if (DEBTOR_SERVICE_PROVIDER_ID) {
      const activationAuth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
      const activationHeaders = buildHeaders(activationAuth.access_token);
      const payload = {
        payer: {
          fiscalCode: fiscalCode,
          rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
        }
      };

      const res = http.post(endpoints.activations, JSON.stringify(payload), { headers: activationHeaders });
      check(res, { 'activation 201': (r) => r.status === 201 });

      if (res.status !== 201) {
        throw new Error(`❌ Failed to create activation for ${fiscalCode}. Status: ${res.status}`);
      }
    }
  }

  const auth = setupAuth(ActorCredentials.RTP_CONSUMER);
  const accessToken = auth.access_token;

  return createDeliveryStatusDataInBatch({
    accessToken,
    targetRequests: TARGET_REQUESTS,
    batchSize: BATCH_SIZE,
    delayBetweenBatches: DELAY_BETWEEN_BATCHES,
    debtorFiscalCode: fiscalCode,
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
 */
export function handleSummary(data) {
  const inputs = (data.setup_data || []).filter(
    (entry) => entry && entry.noticeNumber && entry.payeeId
  );

  console.log(`💾 Saving ${inputs.length} delivery-status inputs to file: ${FILE_PATH}`);

  return {
    [FILE_PATH]: JSON.stringify(inputs, null, 2),
  };
}
