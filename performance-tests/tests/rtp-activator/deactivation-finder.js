import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, endpoints, determineStage, getOptions } from '../../utils/utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';
import { createActivationsInBatch, shuffleArray, distributeItemsAmongGroups } from '../../utils/batch-utils.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createDeactivationTeardown } from '../../utils/teardown-utils.js';

const START_TIME = Date.now();
const { DEBTOR_SERVICE_PROVIDER_ID } = __ENV;
const VU_COUNT_SET = 50;

const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

export let options = {
  ...getOptions('stress_test_fixed_user', 'deactivate'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: 500,
      maxDuration: '30m',
      gracefulStop: '30m',
      exec: 'deactivate'
    }
  }
};

let testCompleted = false;

export function setup() {
  const auth = setupAuth();
  
  const activationIds = createActivationsInBatch({
    accessToken: auth.access_token,
    targetActivations: 500,
    batchSize: 50,
    delayBetweenBatches: 2,
    serviceProviderId: DEBTOR_SERVICE_PROVIDER_ID
  });
  
  shuffleArray(activationIds);
  
  const activationChunks = distributeItemsAmongGroups(activationIds, VU_COUNT_SET);
  
  console.log(`Activations distributed among ${VU_COUNT_SET} virtual users:`);
  for (let i = 0; i < VU_COUNT_SET; i++) {
    console.log(`- VU #${i + 1}: ${activationChunks[i].length} activations`);
  }
  
  return {
    access_token: auth.access_token,
    activationChunks: activationChunks,
    totalActivations: activationIds.length,
    deactivatedCount: 0,
    allCompleted: false
  };
}

export function deactivate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds),
    deactivatedCount: data.deactivatedCount,
    vu: __VU
  };

  currentRPS.add(1, tags);

  if (testCompleted) {
    console.log(`⏹️ Test already completed. VU #${__VU} staying idle to keep dashboard active...`);
    sleep(30);
    return {
      status: 200,
      message: 'Test already completed, waiting for dashboard viewing',
      noMetrics: true
    };
  }

  const vuIndex = __VU - 1;

  if (!data.activationChunks[vuIndex]) {
    console.log(`⚠️ VU #${__VU}: No activation chunk assigned. Termination.`);
    return { status: 400, message: 'No activation chunk assigned', noMetrics: true };
  }

  const myActivations = data.activationChunks[vuIndex];

  if (data.currentIndices === undefined) {
    data.currentIndices = {};
  }
  if (data.currentIndices[vuIndex] === undefined) {
    data.currentIndices[vuIndex] = 0;
  }

  if (data.vuDeactivatedCount === undefined) {
    data.vuDeactivatedCount = {};
  }
  if (data.vuDeactivatedCount[vuIndex] === undefined) {
    data.vuDeactivatedCount[vuIndex] = 0;
  }

  if (data.vuDeactivatedCount[vuIndex] >= myActivations.length) {
    console.log(`✓ VU #${__VU}: Completed all ${myActivations.length} deactivations assigned.`);
    sleep(5);
    return {
      status: 200,
      message: `VU #${__VU} completed all deactivations, idle for dashboard`,
      noMetrics: true
    };
  }

  const currentIndex = data.currentIndices[vuIndex];
  const activationItem = myActivations[currentIndex];

  if (activationItem.deactivated) {
    data.currentIndices[vuIndex] = (currentIndex + 1) % myActivations.length;
    return deactivate(data);
  }

  const headers = buildHeaders(data.access_token);
  const url = `${endpoints.deactivations}/${activationItem.id}`;

  const start = Date.now();
  const res = http.del(url, null, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 204) {
    successCounter.add(1, tags);

    activationItem.deactivated = true;
    data.vuDeactivatedCount[vuIndex]++;
    data.deactivatedCount++;

    if (data.deactivatedCount % 50 === 0 || data.vuDeactivatedCount[vuIndex] === data.activationChunks[vuIndex].length) {
      console.log(`✓ VU #${__VU}: ${data.vuDeactivatedCount[vuIndex]}/${data.activationChunks[vuIndex].length} deactivations completed (Total: ${data.deactivatedCount}/${data.totalActivations})`);
    }

    if (data.deactivatedCount >= data.totalActivations && !data.allCompleted) {
      data.allCompleted = true;
      testCompleted = true;
      console.log(`✅ TEST COMPLETED: All ${data.totalActivations} activations have been deactivated!`);
      console.log(`Total execution time: ${Math.round(elapsedSeconds)} seconds`);
      console.log(`Dashboard will remain active for viewing results.`);
      return {
        status: 204,
        message: 'Test completed successfully, dashboard still active',
        noMetrics: false
      };
    }
  } else {
    failureCounter.add(1, tags);
    console.error(`❌ VU #${__VU}: Failed deactivation for ID ${activationItem.id}: Status ${res.status}`);
  }

  check(res, {
    'deactivation: status is 204': (r) => r.status === 204
  });

  data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % myActivations.length;

  sleep(1);

  return res;
}

const testCompletedRef = { value: false };

export const teardown = createDeactivationTeardown({
  START_TIME,
  VU_COUNT: VU_COUNT_SET,
  testCompletedRef
});

Object.defineProperty(testCompletedRef, 'value', {
  get: () => testCompleted,
  set: (newValue) => { testCompleted = newValue; }
});

export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'MULTI-VU DEACTIVATION STRESS TEST',
  countTag: 'deactivatedCount',
  reportPrefix: 'deactivation',
  VU_COUNT: VU_COUNT_SET
});
