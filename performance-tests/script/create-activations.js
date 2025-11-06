import {ActorCredentials, setupAuth} from "../utils/utils.js";
import { createActivationsInBatch } from "../utils/batch-utils.js";

const DEBTOR_SERVICE_PROVIDER_ID = __ENV.DEBTOR_SERVICE_PROVIDER_ID;
const FILE_PATH = 'json-file/rtp-activator/activations.json';

export let options = {
    setupTimeout: "30m",
};

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

export default function () {}

export function handleSummary(data) {
    const activations = data.setup_data || [];
    console.log(`💾 Saving ${activations.length} activations to file: ${FILE_PATH}`);

    return {
        [FILE_PATH]: JSON.stringify(activations, null, 2),
    };
}
