import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, endpoints, determineStage, getOptions } from '../../utils/utils.js';
import { createStandardMetrics, analyzeTimeWindowsData, findBreakingPoint, findFirstFailure, getMaxTagCount, calculateOverallStats } from '../../utils/metrics-utils.js';
import { createActivationsInBatch, shuffleArray, distributeItemsAmongGroups } from '../../utils/batch-utils.js';
import { generateTextReport, generateVuStatsText, generateTeardownInfo } from '../../utils/reporting-utils.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

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
      gracefulStop: '10m',
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
    sleep(5);
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

export function teardown(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  let actualDeactivatedCount = 0;
  let totalActivations = 0;

  if (data && data.activationChunks) {
    data.activationChunks.forEach(chunk => {
      if (chunk) {
        totalActivations += chunk.length;
        actualDeactivatedCount += chunk.filter(item => item.deactivated).length;
      }
    });
  }

  let vuStats = [];
  if (data && data.vuDeactivatedCount) {
    for (let i = 0; i < VU_COUNT_SET; i++) {
      const vuDeactivated = data.vuDeactivatedCount[i] || 0;
      const vuTotal = data.activationChunks && data.activationChunks[i] ? data.activationChunks[i].length : 0;
      vuStats.push({
        vu: i + 1,
        deactivated: vuDeactivated,
        total: vuTotal,
        percentage: vuTotal > 0 ? (vuDeactivated / vuTotal * 100).toFixed(1) : 0
      });
    }
  }

  const finalState = {
    testCompleted: testCompleted,
    totalActivations: totalActivations,
    deactivatedCount: actualDeactivatedCount,
    expectedDeactivations: data ? data.deactivatedCount : 0,
    testDuration: Math.round(elapsedSeconds),
    vuStats: vuStats
  };

  if (testCompleted) {
    console.log('====================================');
    console.log(`TEST COMPLETED SUCCESSFULLY!`);
    console.log(`All ${finalState.totalActivations} activations have been deactivated.`);
    console.log(`Total execution time: ${finalState.testDuration} seconds`);
    console.log('====================================');
  } else {
    console.log('====================================');
    console.log('TEST TERMINATED BEFORE COMPLETION');
    console.log(`Deactivated ${finalState.deactivatedCount} activations out of ${finalState.totalActivations} (${(finalState.deactivatedCount / finalState.totalActivations * 100).toFixed(1)}%).`);
    console.log(`Total execution time: ${finalState.testDuration} seconds`);
    console.log('====================================');
  }

  console.log('STATISTICS FOR VIRTUAL USER:');
  vuStats.forEach(stat => {
    console.log(`- VU #${stat.vu}: ${stat.deactivated}/${stat.total} (${stat.percentage}%)`);
  });

  const vuStatsText = generateVuStatsText(vuStats);
  finalState.additionalReportContent = generateTeardownInfo(finalState, vuStatsText);

  return finalState;
}

export function handleSummary(data) {
  console.log('Generating enhanced summary for deactivation stress test...');

  const timeWindowsAnalysis = analyzeTimeWindowsData(data);

  const breakingPoint = findBreakingPoint(timeWindowsAnalysis);
  const firstFailure = findFirstFailure(timeWindowsAnalysis);
  const maxDeactivatedCount = getMaxTagCount(data, 'deactivatedCount');

  if (breakingPoint) {
    breakingPoint.deactivatedCount = maxDeactivatedCount;
  }
  if (firstFailure) {
    firstFailure.deactivatedCount = maxDeactivatedCount;
  }

  const overallStats = calculateOverallStats(data, {
    startTime: START_TIME,
    breakingPoint: breakingPoint,
    firstFailure: firstFailure,
    maxDeactivatedCount: maxDeactivatedCount
  });

  const reportText = generateTextReport({
    testName: 'MULTI-VU DEACTIVATION STRESS TEST',
    testStatus: testCompleted ? "COMPLETED" : "INTERRUPTED",
    vuCount: VU_COUNT_SET,
    overallStats: overallStats,
    breakingPoint: breakingPoint,
    firstFailure: firstFailure,
    additionalContent: data.setupData && data.setupData.additionalReportContent ? data.setupData.additionalReportContent : ''
  });

  return {
    'stdout': textSummary(data, { indent: '  ', enableColors: true }),
    'deactivation-stress-analysis.json': JSON.stringify({
      summary: overallStats,
      timeWindowsAnalysis: timeWindowsAnalysis,
      metrics: Object.fromEntries(
        Object.entries(data.metrics).map(([k, v]) => [k, {
          avg: v.values ? v.values.avg : null,
          p95: v.values ? v.values['p(95)'] : null,
          count: v.values ? v.values.count : null
        }])
      )
    }, null, 2),
    'deactivation-report.txt': reportText
  };
}
