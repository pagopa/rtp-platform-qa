import { ActorCredentials, setupAuth } from "../utils/utils.js";
import { createSendInBatch } from "../utils/batch-utils.js";

const SERVICE_PROVIDER_ID = __ENV.SERVICE_PROVIDER_ID;
const FILE_PATH = 'json-file/rtp-sender/resourceIds.json';

export let options = {
    setupTimeout: '30m',
};


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

export default function () {}

export function handleSummary(data) {
    const idsOnly = (data.setup_data || [])
        .map((r) => r?.id || r.resourceId)
        .filter(Boolean);

    console.log(`💾 Saving ${idsOnly.length} resourceIds to file: ${FILE_PATH}`);

    return {
        [FILE_PATH]: JSON.stringify(idsOnly, null, 2),
    };
}
