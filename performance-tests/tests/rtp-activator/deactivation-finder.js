import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, randomFiscalCode, buildHeaders, endpoints, determineStage, stages, getOptions } from '../../utils/utils.js';
import { Counter, Trend } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

const START_TIME = Date.now();
const { DEBTOR_SERVICE_PROVIDER_ID } = __ENV;

const currentRPS = new Counter('current_rps');
const failureCounter = new Counter('failures');
const successCounter = new Counter('successes');
const responseTimeTrend = new Trend('response_time');

const VU_COUNT_SET = 10;

export let options = {
  ...getOptions('stress_test_fixed_user', 'deactivate'),
  scenarios: {
    stress_test_fixed_user: {
      executor: 'shared-iterations',
      vus: VU_COUNT_SET,
      iterations: 500,
      maxDuration: '30m',
      exec: 'deactivate'
    }
  }
};


let testCompleted = false;

export function setup() {
  const auth = setupAuth();
  const headers = buildHeaders(auth.access_token);

  console.log('Creation of test activations for deactivation stress test...');

  const targetActivations = 500;
  const batchSize = 50;
  const delayBetweenBatches = 2;

  const activationIds = [];

  for (let batch = 0; batch < Math.ceil(targetActivations / batchSize); batch++) {
    const batchRequests = [];
    const batchFiscalCodes = [];

    for (let i = 0; i < batchSize && (batch * batchSize + i) < targetActivations; i++) {
      const debtor_fc = randomFiscalCode();
      batchFiscalCodes.push(debtor_fc);
      const payload = { payer: { fiscalCode: debtor_fc, rtpSpId: DEBTOR_SERVICE_PROVIDER_ID } };

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

    console.log(`Batch ${batch + 1}: ${successCount} activation created (${failureCount} failed), total: ${activationIds.length}`);

    if (batch < Math.ceil(targetActivations / batchSize) - 1) {
      sleep(delayBetweenBatches);
    }
  }

  console.log(`Setup completed: ${activationIds.length} activation ready for deactivation stress test`);

  shuffleArray(activationIds);

  const VU_COUNT = VU_COUNT_SET;
  const activationChunks = [];

  for (let i = 0; i < VU_COUNT; i++) {
    activationChunks[i] = [];
  }

  activationIds.forEach((item, index) => {
    const chunkIndex = index % VU_COUNT;
    activationChunks[chunkIndex].push(item);
  });

  console.log(`Activations distributed among ${VU_COUNT} virtual users:`);
  for (let i = 0; i < VU_COUNT; i++) {
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

function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
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
    console.log(`⏹️ Test already completed. VU #${__VU} in termination...`);
    return {
      status: 200,
      message: 'Test already completed',
      noMetrics: true,
      __TEARDOWN: true
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
    return {
      status: 200,
      message: `VU #${__VU} completed all deactivations`,
      noMetrics: true,
      __TEARDOWN: true
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
      return {
        status: 204,
        message: 'Test completed successfully',
        noMetrics: false,
        __TEARDOWN: true
      };
    }
  } else {
    failureCounter.add(1, tags);

    console.error(`❌ VU #${__VU}: Failed deactivation for ID ${activationItem.id}: Status ${res.status}`);
  }

  check(res, {
    'deactivation: status is 204': (r) => r.status === 204
  });

  data.currentIndices[vuIndex] = (data.currentIndices[vuIndex] + 1) % data.activationChunks[vuIndex].length;

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
    for (let i = 0; i < 10; i++) {
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

  let vuStatsText = 'STATISTICS FOR VIRTUAL USER:\n';
  vuStats.forEach(stat => {
    vuStatsText += `- VU #${stat.vu}: ${stat.deactivated}/${stat.total} (${stat.percentage}%)\n`;
  });

  finalState.additionalReportContent = `
ADDITIONAL INFORMATION FROM TEARDOWN:
- Test completed: ${finalState.testCompleted ? "Yes" : "No"}
- Total activations: ${finalState.totalActivations}
- Deactivated activations: ${finalState.deactivatedCount} (${(finalState.deactivatedCount / finalState.totalActivations * 100).toFixed(1)}%)
- Duration (seconds): ${finalState.testDuration}

${vuStatsText}
`;

  return finalState;
}

export function handleSummary(data) {
  console.log('Generating enhanced summary for deactivation stress test...');

  const timeWindowsAnalysis = {};

  if (data.metrics.response_time && data.metrics.response_time.values) {
    for (const [key, value] of Object.entries(data.metrics.response_time.values)) {
      if (key.startsWith('timeWindow:') && !key.includes('stage:')) {
        const timeWindow = key.replace('timeWindow:', '');
        if (!timeWindowsAnalysis[timeWindow]) {
          timeWindowsAnalysis[timeWindow] = {
            responseTime: value,
            successes: 0,
            failures: 0,
            requests: 0,
            deactivatedCount: 0
          };
        } else {
          timeWindowsAnalysis[timeWindow].responseTime = value;
        }
      }
    }
  }

  if (data.metrics.successes && data.metrics.successes.values) {
    for (const [key, value] of Object.entries(data.metrics.successes.values)) {
      if (key.startsWith('timeWindow:') && !key.includes('stage:')) {
        const timeWindow = key.replace('timeWindow:', '');
        if (!timeWindowsAnalysis[timeWindow]) {
          timeWindowsAnalysis[timeWindow] = {
            successes: value.count,
            failures: 0,
            requests: value.count,
            responseTime: {}
          };
        } else {
          timeWindowsAnalysis[timeWindow].successes = value.count;
          timeWindowsAnalysis[timeWindow].requests += value.count;
        }
      }
    }
  }

  if (data.metrics.failures && data.metrics.failures.values) {
    for (const [key, value] of Object.entries(data.metrics.failures.values)) {
      if (key.startsWith('timeWindow:') && !key.includes('stage:')) {
        const timeWindow = key.replace('timeWindow:', '');
        if (!timeWindowsAnalysis[timeWindow]) {
          timeWindowsAnalysis[timeWindow] = {
            successes: 0,
            failures: value.count,
            requests: value.count,
            responseTime: {}
          };
        } else {
          timeWindowsAnalysis[timeWindow].failures = value.count;
          timeWindowsAnalysis[timeWindow].requests += value.count;
        }
      }
    }
  }

  for (const window in timeWindowsAnalysis) {
    const windowData = timeWindowsAnalysis[window];
    if (windowData.requests > 0) {
      windowData.successRate = (windowData.successes / windowData.requests) * 100;
      windowData.failureRate = (windowData.failures / windowData.requests) * 100;
    }
  }

  let breakingPoint = null;
  const timeWindows = Object.keys(timeWindowsAnalysis).sort((a, b) => parseInt(a) - parseInt(b));

  for (const window of timeWindows) {
    const windowData = timeWindowsAnalysis[window];
    if (windowData && windowData.requests > 10 && windowData.failureRate > 10) {
      breakingPoint = {
        timeWindow: window,
        secondsFromStart: parseInt(window) * 10,
        failureRate: windowData.failureRate,
        requests: windowData.requests,
        deactivatedCount: 0,
        avgResponseTime: windowData.responseTime.avg
      };
      break;
    }
  }

  let firstFailure = null;
  for (const window of timeWindows) {
    const windowData = timeWindowsAnalysis[window];
    if (windowData && windowData.failures > 0) {
      firstFailure = {
        timeWindow: window,
        secondsFromStart: parseInt(window) * 10,
        failures: windowData.failures
      };
      break;
    }
  }

  let maxDeactivatedCount = 0;
  if (data.metrics.successes && data.metrics.successes.values) {
    for (const [key, value] of Object.entries(data.metrics.successes.values)) {
      if (key.includes('deactivatedCount:')) {
        const countMatch = key.match(/deactivatedCount:(\d+)/);
        if (countMatch && countMatch[1]) {
          const count = parseInt(countMatch[1]);
          if (count > maxDeactivatedCount) {
            maxDeactivatedCount = count;
          }
        }
      }
    }
  }

  if (breakingPoint) {
    breakingPoint.deactivatedCount = maxDeactivatedCount;
  }

  if (firstFailure) {
    firstFailure.deactivatedCount = maxDeactivatedCount;
  }

  const overallStats = {
    totalRequests: data.metrics.iterations.count,
    successfulDeactivations: data.metrics.successes ? data.metrics.successes.count : 0,
    failedDeactivations: data.metrics.failures ? data.metrics.failures.count : 0,
    successRate: (data.metrics.checks && data.metrics.checks.count > 0) ?
      (data.metrics.checks.passes / data.metrics.checks.count * 100) : 0,
    failureRate: (data.metrics.checks && data.metrics.checks.count > 0) ?
      (data.metrics.checks.fails / data.metrics.checks.count * 100) : 0,
    avgResponseTime: data.metrics.response_time ? data.metrics.response_time.values.avg : 0,
    p95ResponseTime: data.metrics.response_time ? data.metrics.response_time.values['p(95)'] : 0,
    breakingPoint: breakingPoint,
    firstFailure: firstFailure,
    testDuration: Math.round((Date.now() - START_TIME) / 1000),
    totalDeactivations: maxDeactivatedCount
  };

  const testStatus = testCompleted ? "COMPLETED" : "INTERRUPTED";

  const reportText = `
========== MULTI-VU DEACTIVATION STRESS TEST REPORT ==========

TEST STATUS: ${testStatus}
VIRTUAL USERS: VU #${VU_COUNT_SET}

Overall Statistics:
- Total requests: ${overallStats.totalRequests}
- Successful deactivations: ${overallStats.successfulDeactivations}
- Failed deactivations: ${overallStats.failedDeactivations}
- Success rate: ${overallStats.successRate.toFixed(2)}%
- Failure rate: ${overallStats.failureRate.toFixed(2)}%
- Average response time: ${overallStats.avgResponseTime.toFixed(2)} ms
- P95 response time: ${overallStats.p95ResponseTime.toFixed(2)} ms
- Total test duration: ${overallStats.testDuration} seconds
- Total deactivations: ${overallStats.totalDeactivations}

${breakingPoint ? `
BREAKING POINT IDENTIFIED:
- After ${breakingPoint.deactivatedCount} deactivations
- At ${breakingPoint.secondsFromStart} seconds from test start
- With failure rate: ${breakingPoint.failureRate.toFixed(2)}%
- Average response time: ${breakingPoint.avgResponseTime.toFixed(2)} ms` :
      'NO BREAKING POINT IDENTIFIED during the test'}

${firstFailure ? `
FIRST FAILURE:
- After ${firstFailure.deactivatedCount} deactivations
- At ${firstFailure.secondsFromStart} seconds from test start
- Number of failures: ${firstFailure.failures}` :
      'NO FAILURE occurred during the test'}

${data.setupData && data.setupData.additionalReportContent ? data.setupData.additionalReportContent : ''}
==========================================================
`;

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