import http from 'k6/http';
import { sleep } from 'k6';
import {
  randomFiscalCode,
  buildHeaders,
  endpoints,
  generatePositiveLong
} from './utils.js';
import {buildGpdMessagePayload, buildSendPayload} from "./sender-payloads.js";
import {senderConfig} from "../config/config.js";
import {uuidv4} from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

/**
 * Create a batch of activations for testing purposes.
 *
 * @param {Object} params - Function parameters
 * @param {string} params.accessToken - Access token for the API
 * @param {number} params.targetActivations - Total number of activations to create
 * @param {number} params.batchSize - Size of each batch of requests (default: 50)
 * @param {number} params.delayBetweenBatches - Seconds to wait between batches (default: 2)
 * @param {string} params.serviceProviderId - ID of the service provider
 * @returns {Array} Array of activation objects with id, fiscalCode, and deactivated status
 */
export function createActivationsInBatch({
  accessToken,
  targetActivations,
  batchSize = 50,
  delayBetweenBatches = 2,
  serviceProviderId
}) {
  console.log(`Creating ${targetActivations} test activations in batches of ${batchSize}...`);

  const headers = buildHeaders(accessToken);
  const activationIds = [];

  for (let batch = 0; batch < Math.ceil(targetActivations / batchSize); batch++) {
    const batchRequests = [];
    const batchFiscalCodes = [];

    for (let i = 0; i < batchSize && (batch * batchSize + i) < targetActivations; i++) {
      const debtor_fc = randomFiscalCode();
      batchFiscalCodes.push(debtor_fc);
      const payload = { payer: { fiscalCode: debtor_fc, rtpSpId: serviceProviderId } };

      batchRequests.push({
        method: 'POST',
        url: endpoints.activations,
        body: JSON.stringify(payload),
        params: { headers, tags: { batchId: batch, itemId: i } }
      });
    }

    const responses = http.batch(batchRequests);

    let successCount = 0;
    let failureCount = 0;

    responses.forEach((res, index) => {
      if (res.status === 201) {
        successCount++;

        let activationId;
        if (res.headers['Location']) {
          activationId = res.headers['Location'].split('/').pop();
        } else if (res.json('activationId')) {
          activationId = res.json('activationId');
        } else {
          try {
            const body = JSON.parse(res.body);
            activationId = body.activationId || null;
          } catch (e) {
            console.warn(`⚠️ Failed to parse response body for fiscalCode: ${batchFiscalCodes[index]}, ex: ${e}`);
          }
        }

        if (activationId) {
          activationIds.push({
            id: activationId,
            fiscalCode: batchFiscalCodes[index],
            deactivated: false
          });
        } else {
          console.error(`⚠️ Activation successful but no ID found for fiscalCode: ${batchFiscalCodes[index]}`);
        }
      } else {
        failureCount++;
        console.error(`❌ Failed activation for fiscalCode ${batchFiscalCodes[index]}: Status ${res.status}`);
      }
    });

    console.log(`Batch ${batch + 1}: ${successCount} activations created (${failureCount} failed), total: ${activationIds.length}`);

    if (batch < Math.ceil(targetActivations / batchSize) - 1) {
      sleep(delayBetweenBatches);
    }
  }

  console.log(`Batch creation completed: ${activationIds.length} activations ready for testing`);
  return activationIds;
}

/**
 * Sends RTP requests in batches using HTTP batch calls.
 *
 * @param {Object} params - Function parameters.
 * @param {string} params.accessToken - Access token used to authorize the requests.
 * @param {number} params.targetRequests - Total number of RTP requests to send.
 * @param {number} [params.batchSize=50] - Number of requests per batch.
 * @param {number} [params.delayBetweenBatches=2] - Delay (in seconds) between batches.
 * @param {string} params.debtorFiscalCode - Debtor fiscal code used in the request payload.
 *
 * @returns {Array<{id: string, debtorFiscalCode: string}>} List of successfully created RTP request IDs.
 */
export function sendRtpInBatch({
  accessToken,
  targetRequests,
  batchSize = 50,
  delayBetweenBatches = 2,
  debtorFiscalCode,
}) {
  console.log(`Sending ${targetRequests} RTP requests in batches of ${batchSize}...`);

  if (!debtorFiscalCode) {
    throw new Error("❌ debtorFiscalCode cannot be null");
  }

  const headers = buildHeaders(accessToken);
  const requestIds = [];
  let totalSuccess = 0;
  let totalFailure = 0;

  for (let batch = 0; batch < Math.ceil(targetRequests / batchSize); batch++) {
    const batchRequests = [];

    for (let i = 0; i < batchSize && (batch * batchSize + i) < targetRequests; i++) {
      const payload = buildSendPayload(debtorFiscalCode);

      batchRequests.push({
        method: 'POST',
        url: endpoints.sendRtp,
        body: JSON.stringify(payload),
        params: { headers },
      });
    }

    const responses = http.batch(batchRequests);
    let batchSuccess = 0;

    responses.forEach((res) => {
      if (res.status >= 200 && res.status < 300) {
        batchSuccess++;

        let resourceId = null;
        if (res.headers?.['Location']) {
          resourceId = res.headers['Location'].split('/').pop();
        }
        if (!resourceId) {
          try {
            const body = JSON.parse(res.body);
            resourceId = body?.resourceId || body?.id || null;
          } catch (e) {
            console.warn(`⚠️ Failed to parse response body. ex: ${e}`);
          }
        }

        if (resourceId) {
          requestIds.push({
            id: resourceId,
            debtorFiscalCode,
          });
        }
      }
    });

    totalSuccess += batchSuccess;
    totalFailure += (responses.length - batchSuccess);

    console.log(`Batch ${batch + 1}: ${batchSuccess} RTP requests sent (${responses.length - batchSuccess} failed), total: ${requestIds.length}`);

    if (batch < Math.ceil(targetRequests / batchSize) - 1) {
      sleep(delayBetweenBatches);
    }
  }

  console.log(`Batch send completed: ${requestIds.length} RTP requests ready (${totalSuccess} success, ${totalFailure} failed)`);
  return requestIds;
}

/**
 * Cancels RTP requests in batches using HTTP batch calls.
 *
 * @param {Object} params - Function parameters.
 * @param {string} params.accessToken - Access token used to authorize the requests.
 * @param {Array<{id: string, payerId?: string}>} params.resourceIds - List of RTP resource IDs to cancel.
 * @param {number} [params.batchSize=50] - Number of cancel requests per batch.
 * @param {number} [params.delayBetweenBatches=1] - Delay (in seconds) between batches.
 *
 * @returns {Array<{id: string, payerId?: string}>} List of successfully canceled RTP requests.
 */
export function cancelRtpInBatch({
  accessToken,
  resourceIds,
  batchSize = 50,
  delayBetweenBatches = 1,
}) {

  console.log(`Cancelling ${resourceIds.length} RTP requests in batches of ${batchSize}...`);

  const headers = buildHeaders(accessToken);
  const basePath = `${senderConfig.sender_base}/rtps`;
  const cancelledIds = [];
  let successCount = 0;
  let failureCount = 0;

  for (let batch = 0; batch < Math.ceil(resourceIds.length / batchSize); batch++) {
    const batchRequests = [];

    for (let i = 0; i < batchSize && (batch * batchSize + i) < resourceIds.length; i++) {
      const resourceId = resourceIds[batch * batchSize + i].id;
      const fullUrl = `${basePath}/${resourceId}/cancel`;

      batchRequests.push({
        method: 'POST',
        url: fullUrl,
        params: { headers },
      });
    }

    const responses = http.batch(batchRequests);

    let batchSuccess = 0;
    responses.forEach((res, index) => {
      if (res.status >= 200 && res.status < 300) {
        batchSuccess++;
        cancelledIds.push(resourceIds[batch * batchSize + index]);
      }
    });

    successCount += batchSuccess;
    failureCount += (responses.length - batchSuccess);

    console.log(`Batch ${batch + 1}: ${batchSuccess} RTP requests cancelled (${responses.length - batchSuccess} failed), total: ${cancelledIds.length}`);

    if (batch < Math.ceil(resourceIds.length / batchSize) - 1) {
      sleep(delayBetweenBatches);
    }
  }

  console.log(`Batch cancel completed: ${cancelledIds.length} RTP requests cancelled (${successCount} success, ${failureCount} failed)`);
  return cancelledIds;
}

/**
 * Creates GPD messages in batches and returns the successful operation IDs.
 *
 * @param {Object} params - Function parameters.
 * @param {string} params.accessToken - Access token used to authorize the requests.
 * @param {number} params.targetRequests - Total number of GPD messages to create.
 * @param {number} [params.batchSize=100] - Number of requests per batch.
 * @param {number} [params.delayBetweenBatches=2] - Delay (in seconds) between batches.
 * @param {string} params.debtorFiscalCode - Debtor fiscal code used in the payload.
 * @param {string} params.operation - GPD operation type.
 * @param {string} params.status - GPD message status.
 * @param {string} params.ecTaxCode - Entity creditor tax code.
 * @param {string|null} [params.psp_tax_code] - PSP tax code.
 * @returns {string[]} List of successful operation IDs.
 */
export function createGpdMessageInBatch({
  accessToken,
  targetRequests,
  batchSize = 100,
  delayBetweenBatches = 2,
  debtorFiscalCode,
  operation,
  status,
  ecTaxCode,
  psp_tax_code,
}) {
  console.log(`Sending ${targetRequests} GpdMessage requests in batches of ${batchSize}...`);

  if (!accessToken){
    throw new Error("❌ accessToken cannot be null");
  }

  if (!debtorFiscalCode) {
    throw new Error("❌ debtorFiscalCode cannot be null");
  }

  if (!operation) {
    throw new Error("❌ operation cannot be null");
  }

  if (!status) {
    throw new Error("❌ status cannot be null");
  }

  if (!ecTaxCode) {
    throw new Error("❌ ecTaxCode cannot be null");
  }

  const operationIds = [];
  let totalSuccess = 0;
  let totalFailure = 0;

  for (let batch = 0; batch < Math.ceil(targetRequests / batchSize); batch++) {
    const batchRequests = [];
    const batchOperationIds = [];

    for (let i = 0; i < batchSize && (batch * batchSize + i) < targetRequests; i++) {
      const operationId = String(generatePositiveLong());

      const payload = buildGpdMessagePayload(
          debtorFiscalCode,
          operationId,
          operation,
          status,
          ecTaxCode,
          psp_tax_code
      );

      batchOperationIds.push(operationId);

      batchRequests.push({
        method: 'POST',
        url: endpoints.gpdMessage,
        body: JSON.stringify(payload),
        params: {
          headers: {
            ...buildHeaders(accessToken),
            "Idempotency-Key": uuidv4(),
          },
        },
      });
    }

    const responses = http.batch(batchRequests);
    let batchSuccess = 0;

    responses.forEach((res, index) => {
      if (res.status >= 200 && res.status < 300) {
        batchSuccess++;
        operationIds.push(batchOperationIds[index]);
      } else {
        console.error(
            `❌ GpdMessage create failed: ${res.status}`
        );
      }
    });

    totalSuccess += batchSuccess;
    totalFailure += (responses.length - batchSuccess);

    console.log(
        `Batch ${batch + 1}: ${batchSuccess} GpdMessage requests sent (${responses.length - batchSuccess} failed), total: ${operationIds.length}`
    );

    if (batch < Math.ceil(targetRequests / batchSize) - 1) {
      sleep(delayBetweenBatches);
    }
  }

  console.log(
      `Batch send completed: ${operationIds.length} GpdMessage ready (${totalSuccess} success, ${totalFailure} failed)`
  );

  return operationIds;
}

/**
 *
 * @param {Array} array - Array to shuffle
 */
export function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

/**
 * Distribute items of an array among a specified number of groups
 *
 * @param {Array} items - Array of items to distribute
 * @param {number} groupCount - Number of groups to distribute the items among
 * @returns {Array} Array of arrays, each subarray contains the items for one group
 */
export function distributeItemsAmongGroups(items, groupCount) {
  const chunks = [];

  for (let i = 0; i < groupCount; i++) {
    chunks[i] = [];
  }

  items.forEach((item, index) => {
    const chunkIndex = index % groupCount;
    chunks[chunkIndex].push(item);
  });

  return chunks;
}
