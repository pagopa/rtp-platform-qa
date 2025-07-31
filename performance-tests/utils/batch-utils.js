import http from 'k6/http';
import { sleep } from 'k6';
import { randomFiscalCode, buildHeaders, endpoints } from './utils.js';

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
            console.warn(`⚠️ Failed to parse response body for fiscalCode: ${batchFiscalCodes[index]}`);
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
