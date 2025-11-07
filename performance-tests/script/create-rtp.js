import { ActorCredentials, setupAuth } from "../utils/utils.js";
import { createSendInBatch } from "../utils/batch-utils.js";

/**
 * @file RTP Sender – Batch setup (k6)
 * @description
 * Generates and sends RTP requests in batches during the k6 `setup()` phase and persists
 * only the resulting `resourceId`s to a JSON file via `handleSummary()`.
 *
 * ## Inputs
 * - Environment variables:
 * - `SERVICE_PROVIDER_ID` (required): Creditor Service Provider identifier used as `payerId`.
 * - `TARGET_REQUESTS` (number, optional, default: 2000): total RTPs to send.
 * - `BATCH_SIZE` (number, optional, default: 50): requests per batch.
 * - `DELAY_BETWEEN_BATCHES` (number, seconds, optional, default: 1): delay between batches.
 *
 * ## Outputs
 * - JSON file: `json-file/rtp-sender/resourceIds.json` containing an array of `resourceId` strings.
 */

/** Debtor/Creditor Service Provider ID from environment. */
const SERVICE_PROVIDER_ID = __ENV.SERVICE_PROVIDER_ID;

/** Destination file for collected resource IDs. */
const FILE_PATH = 'json-file/rtp-sender/resourceIds.json';

/**
 * k6 options. We extend the setup timeout to accommodate large batch runs.
 * @type {{ setupTimeout: string }}
 */
export let options = {
    setupTimeout: '30m',
};

/**
 * Runtime configuration derived from environment variables.
 * @typedef {Object} Config
 * @property {string} serviceProviderId Creditor Service Provider ID (required).
 * @property {number} targetRequests Total number of RTP send requests to perform.
 * @property {number} batchSize Number of requests per batch.
 * @property {number} delayBetweenBatches Delay in seconds between batches.
 */


/**
 * Reads and validates configuration from environment variables, applying defaults.
 *
 * @returns {Config} Normalized configuration object.
 * @throws {Error} If `SERVICE_PROVIDER_ID` is not provided.
 */
function getConfig() {
    if (!SERVICE_PROVIDER_ID) {
        throw new Error("❌ SERVICE_PROVIDER_ID cannot be null");
    }

    return {
        serviceProviderId: SERVICE_PROVIDER_ID,
        targetRequests: Number(__ENV.TARGET_REQUESTS) || 2000,
        batchSize: Number(__ENV.BATCH_SIZE) || 50,
        delayBetweenBatches: Number(__ENV.DELAY_BETWEEN_BATCHES) || 1,
    };
}

let savedResourceIds = [];

/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as a Creditor Service Provider, then sends RTP requests in batches using
 * `createSendInBatch`. Returns the array of items produced by the batch utility so they are
 * available as `setup_data` to `handleSummary()`.
 *
 * @returns {Array<{ id?: string, resourceId?: string }>} Array of batch results (each containing an id/resourceId).
 */
export function setup() {
    try {
        const config = getConfig();
        console.log("⚙️ Configuration:", config);

        const auth = setupAuth(ActorCredentials.CREDITOR_SERVICE_PROVIDER);

        const resourceIds = createSendInBatch({
            accessToken: auth.access_token,
            targetRequests: config.targetRequests,
            batchSize: config.batchSize,
            delayBetweenBatches: config.delayBetweenBatches,
            payerId: config.serviceProviderId,
        });

        console.log("✅ Number of RTP sent:", resourceIds.length);
        return resourceIds;
    } catch (err) {
        console.error("❌ Error while creating RTP:", err.message);
        return [];
    }
}

/**
 * Default k6 test function (not used). The logic runs entirely in `setup()`.
 */
export default function () {}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Extracts only the resource identifiers from `setup_data` and writes them to a JSON file
 * for later consumption.
 *
 * @param {{ setup_data?: Array<{ id?: string, resourceId?: string }> }} data Object carrying setup output.
 * @returns {Record<string, string>} Map of output filenames to serialized file contents.
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
