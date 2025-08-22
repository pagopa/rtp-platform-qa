import { generateVuStatsText, generateTeardownInfo } from './reporting-utils.js';

/**
 * Creates a standardized teardown function for batch processing tests
 * like activation or deactivation tests.
 * 
 * @param {Object} config - Configuration object
 * @param {number} config.START_TIME - Test start timestamp
 * @param {number} config.VU_COUNT - Number of virtual users
 * @param {string} config.testType - Type of test ('activation', 'deactivation', etc.)
 * @param {boolean} config.testCompletedRef - Reference to the testCompleted variable in the calling file
 * @returns {Function} - A teardown function that can be exported from test files
 */
export function createBatchProcessingTeardown({ START_TIME, VU_COUNT, testType, testCompletedRef }) {
  return function(data) {
    const elapsedSeconds = (Date.now() - START_TIME) / 1000;
    
    let actualProcessedCount = 0;
    let totalItems = 0;
    
    const itemsKey = `${testType}Chunks`;
    const countKey = `${testType}edCount`;
    
    if (data && data[itemsKey]) {
      data[itemsKey].forEach(chunk => {
        if (chunk) {
          totalItems += chunk.length;
          actualProcessedCount += chunk.filter(item => item[testType + 'ed']).length;
        }
      });
    }
    
    let vuStats = [];
    if (data && data.vuProcessedCount) {
      for (let i = 0; i < VU_COUNT; i++) {
        const vuProcessed = data.vuProcessedCount[i] || 0;
        const vuTotal = data[itemsKey] && data[itemsKey][i] ? data[itemsKey][i].length : 0;
        vuStats.push({
          vu: i + 1,
          processed: vuProcessed,
          total: vuTotal,
          percentage: vuTotal > 0 ? (vuProcessed / vuTotal * 100).toFixed(1) : 0
        });
      }
    }
    
    if (data && data.allCompleted) {
      testCompletedRef.value = true;
    }
    
    const finalState = {
      testCompleted: testCompletedRef.value,
      allCompleted: testCompletedRef.value,
      totalItems: totalItems,
      processedCount: actualProcessedCount,
      expectedProcessed: data ? data[countKey] : 0,
      testDuration: Math.round(elapsedSeconds),
      vuStats: vuStats
    };
    
    if (testCompletedRef.value) {
      console.log('====================================');
      console.log(`TEST COMPLETED SUCCESSFULLY!`);
      console.log(`All ${finalState.totalItems} items have been processed.`);
      console.log(`Total execution time: ${finalState.testDuration} seconds`);
      console.log('====================================');
    } else {
      console.log('====================================');
      console.log('TEST TERMINATED BEFORE COMPLETION');
      console.log(`Processed ${finalState.processedCount} out of ${finalState.totalItems} items (${(finalState.processedCount / finalState.totalItems * 100).toFixed(1)}%).`);
      console.log(`Total execution time: ${finalState.testDuration} seconds`);
      console.log('====================================');
    }
    
    console.log(`STATISTICS FOR VIRTUAL USERS:`);
    vuStats.forEach(stat => {
      console.log(`- VU #${stat.vu}: ${stat.processed}/${stat.total} (${stat.percentage}%)`);
    });
    
    const vuStatsText = generateVuStatsText(vuStats, 'processed');
    finalState.additionalReportContent = generateTeardownInfo(finalState, vuStatsText, testType);
    
    return finalState;
  };
}

/**
 * Creates a specialized teardown function for deactivation tests.
 * 
 * @param {Object} config - Configuration object
 * @param {number} config.START_TIME - Test start timestamp
 * @param {number} config.VU_COUNT - Number of virtual users
 * @param {Object} config.testCompletedRef - Reference to the testCompleted variable in the calling file
 * @returns {Function} - A teardown function specifically for deactivation tests
 */
export function createDeactivationTeardown({ START_TIME, VU_COUNT, testCompletedRef }) {
  return function(data) {
    if (data) {
      data.deactivationChunks = data.activationChunks;
      data.vuProcessedCount = data.vuDeactivatedCount;
    }
    
    return createBatchProcessingTeardown({
      START_TIME,
      VU_COUNT,
      testType: 'deactivate',
      testCompletedRef
    })(data);
  };
}

/**
 * Creates a specialized teardown function for activation tests.
 * 
 * @param {Object} config - Configuration object
 * @param {number} config.START_TIME - Test start timestamp
 * @param {number} config.VU_COUNT - Number of virtual users
 * @param {Object} config.testCompletedRef - Reference to the testCompleted variable in the calling file
 * @returns {Function} - A teardown function specifically for activation tests
 */
export function createActivationTeardown({ START_TIME, VU_COUNT, testCompletedRef }) {
  return function(data) {
    if (data) {
      data.activationChunks = data.activationBatches || [];
      data.vuProcessedCount = data.vuActivatedCount;
    }
    
    return createBatchProcessingTeardown({
      START_TIME,
      VU_COUNT,
      testType: 'activate',
      testCompletedRef
    })(data);
  };
}

/**
 * Creates a specialized teardown function for callback tests.
 *
 * @param {Object} config - Configuration object
 * @param {number} config.START_TIME - Test start timestamp
 * @param {number} config.VU_COUNT - Number of virtual users
 * @param {Object} config.testCompletedRef - Reference to the testCompleted variable in the calling file
 * @returns {Function} - A teardown function specifically for callback tests
 */
export function createCallbackTeardown({ START_TIME, VU_COUNT, testCompletedRef }) {
    return function(data) {
        if (data) {
            data.vuProcessedCount = data.vuCallbackCount;
            data.callbackedCount = data.callbackCount;

            if (Array.isArray(data.callbackChunks)) {
                data.callbackChunks = data.callbackChunks.map(chunk =>
                    Array.isArray(chunk)
                        ? chunk.map(item => ({ ...item, callbacked: item.callbacked ?? !!item.processed }))
                        : chunk
                );
            }
        }

        return createBatchProcessingTeardown({
            START_TIME,
            VU_COUNT,
            testType: 'callback',
            testCompletedRef
        })(data);
    };
}

export function createFinderTeardown({ START_TIME, VU_COUNT, testCompletedRef }) {
  return function(data) {
    if (data) {
      data.deactivationChunks = data.activationChunks;
      data.vuProcessedCount = data.vuDeactivatedCount;
    }

    return createBatchProcessingTeardown({
      START_TIME,
      VU_COUNT,
      testType: 'findByFiscalCode',
      testCompletedRef
    })(data);
  };
}
