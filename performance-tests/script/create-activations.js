import {ActorCredentials, setupAuth} from "../utils/utils.js";
import { createActivationsInBatch } from "../utils/batch-utils.js";

/**
 * @file RTP Activator - k6 script
 * @description
 * Creates RTP activations in batches during the k6 `setup()` phase and writes
 * them to a JSON file via `handleSummary()`.
 *
 * ## Environment Variables
 * - `DEBTOR_SERVICE_PROVIDER_ID` (required): Debtor Service Provider identifier.
 * - `TARGET_REQUESTS` (optional, default: 2000): Total number of activations to create.
 * - `BATCH_SIZE` (optional, default: 50): Number of activations per batch.
 * - `DELAY_BETWEEN_BATCHES` (optional, seconds, default: 1): Delay between batches.
 *
 * The activations generated in `setup()` are returned as `setup_data` and then
 * persisted by `handleSummary()` into `json-file/rtp-activator/activations.json`.
 */

/**
 * @typedef {Object} Config
 * @property {string} debtorServiceProviderId Debtor Service Provider ID (required).
 * @property {number} targetRequests Total number of activations to generate.
 * @property {number} batchSize Number of activations to include in each batch.
 * @property {number} delayBetweenBatches Delay (in seconds) to wait between batches.
 */

/** Debtor Service Provider ID sourced from the environment. */
const DEBTOR_SERVICE_PROVIDER_ID = __ENV.DEBTOR_SERVICE_PROVIDER_ID;

/** Path where the generated activations will be saved. */
const FILE_PATH = 'json-file/rtp-activator/activations.json';

/**
 * k6 execution options.
 * @type {{ setupTimeout: string }}
 */
export let options = {
    setupTimeout: "30m",
};

/**
 * Reads, validates, and normalizes configuration from environment variables.
 *
 * @returns {Config} The fully validated runtime configuration.
 * @throws {Error} If `DEBTOR_SERVICE_PROVIDER_ID` is not defined.
 */
function getConfig() {
    if (!DEBTOR_SERVICE_PROVIDER_ID) {
        throw new Error("❌ DEBTOR_SERVICE_PROVIDER_ID cannot be null or undefined");
    }

    return {
        debtorServiceProviderId: DEBTOR_SERVICE_PROVIDER_ID,
        targetRequests: Number(__ENV.TARGET_REQUESTS) || 2000,
        batchSize: Number(__ENV.BATCH_SIZE) || 50,
        delayBetweenBatches: Number(__ENV.DELAY_BETWEEN_BATCHES) || 1,
    };
}


/**
 * k6 `setup()` lifecycle function.
 *
 * Authenticates as `DEBTOR_SERVICE_PROVIDER` and creates activations in batches,
 * returning them so they are available as `setup_data` to the test and to
 * `handleSummary()`.
 *
 * @returns {Array<object>} The list of generated activations. Returns an empty array on error.
 */
export async function setup() {
    try {
        const config = getConfig();
        console.log("⚙️ Configuration:", config);

        const auth = setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);

        const activationsInBatch = createActivationsInBatch({
            accessToken: auth.access_token,
            targetActivations: config.targetRequests,
            batchSize: config.batchSize,
            delayBetweenBatches: config.delayBetweenBatches,
            serviceProviderId: config.debtorServiceProviderId,
        });

        console.log("✅ Number of Activations created:", activationsInBatch.length);
        return activationsInBatch;
    } catch (err) {
        console.error("❌ Error while creating RTP:", err.message);
        return [];
    }
}

/**
 * k6 default function (virtual user logic).
 * Not used in this scenario; activations are prepared entirely in `setup()`.
 */
export default function () {}

/**
 * k6 `handleSummary()` lifecycle function.
 *
 * Persists the activations produced by `setup()` to a JSON file so they can
 * be reused after the test run.
 *
 * @param {{ setup_data?: Array<object> }} data Object containing `setup_data` from `setup()`.
 * @returns {Record<string, string>} A map of output filenames to file contents.
 */
export function handleSummary(data) {
    const activations = data.setup_data || [];
    console.log(`💾 Saving ${activations.length} activations to file: ${FILE_PATH}`);

    return {
        [FILE_PATH]: JSON.stringify(activations, null, 2),
    };
}
