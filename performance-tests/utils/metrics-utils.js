import { Counter, Trend } from 'k6/metrics';

/**
 * Create standard metrics for performance tests
 * 
 * @param {string} prefix - Optional prefix for metric names
 * @returns {Object} Object containing the created metrics
 */
export function createStandardMetrics(prefix = '') {
  const prefixStr = prefix ? `${prefix}_` : '';
  return {
    currentRPS: new Counter(`${prefixStr}current_rps`),
    failureCounter: new Counter(`${prefixStr}failures`),
    successCounter: new Counter(`${prefixStr}successes`),
    responseTimeTrend: new Trend(`${prefixStr}response_time`)
  };
}

/**
 * Analyze time windows data from performance test metrics
 *
 * @param {Object} data - Performance test metrics data from k6
 * @returns {Object} Time window analysis of the metrics data
 */
export function analyzeTimeWindowsData(data) {
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
  
  return timeWindowsAnalysis;
}

/**
 * Finds the breaking point in the time windows analysis
 * 
 * @param {Object} timeWindowsAnalysis - Time windows analysis
 * @param {number} failureThreshold - Failure percentage threshold to consider as breaking point (default: 10%)
 * @returns {Object|null} Breaking point information or null if not found
 */
export function findBreakingPoint(timeWindowsAnalysis, failureThreshold = 10) {
  const timeWindows = Object.keys(timeWindowsAnalysis).sort((a, b) => parseInt(a) - parseInt(b));
  
  for (const window of timeWindows) {
    const windowData = timeWindowsAnalysis[window];
    if (windowData && windowData.requests > 10 && windowData.failureRate > failureThreshold) {
      return {
        timeWindow: window,
        secondsFromStart: parseInt(window) * 10,
        failureRate: windowData.failureRate,
        requests: windowData.requests,
        deactivatedCount: 0,
        avgResponseTime: windowData.responseTime.avg
      };
    }
  }
  
  return null;
}

/**
 * Finds the first failure in the time windows analysis
 * 
 * @param {Object} timeWindowsAnalysis - Time windows analysis
 * @returns {Object|null} First failure information or null if not found
 */
export function findFirstFailure(timeWindowsAnalysis) {
  const timeWindows = Object.keys(timeWindowsAnalysis).sort((a, b) => parseInt(a) - parseInt(b));
  
  for (const window of timeWindows) {
    const windowData = timeWindowsAnalysis[window];
    if (windowData && windowData.failures > 0) {
      return {
        timeWindow: window,
        secondsFromStart: parseInt(window) * 10,
        failures: windowData.failures
      };
    }
  }
  
  return null;
}

/**
 * Extracts the maximum count of a given tag from the metrics data
 * 
 * @param {Object} data - Metrics data from k6
 * @param {string} tagName - Name of the tag to search for (e.g. "deactivatedCount")
 * @returns {number} The maximum value found for the specified tag
 */
export function getMaxTagCount(data, tagName) {
  let maxCount = 0;
  
  if (data.metrics.successes && data.metrics.successes.values) {
    for (const [key, value] of Object.entries(data.metrics.successes.values)) {
      if (key.includes(`${tagName}:`)) {
        const countMatch = key.match(new RegExp(`${tagName}:(\\d+)`));
        if (countMatch && countMatch[1]) {
          const count = parseInt(countMatch[1]);
          if (count > maxCount) {
            maxCount = count;
          }
        }
      }
    }
  }
  
  return maxCount;
}

/**
 * Calculates overall statistics from the metrics data
 * 
 * @param {Object} data - Metrics data from k6
 * @param {Object} params - Additional parameters
 * @returns {Object} Overall test statistics
 */
export function calculateOverallStats(data, params = {}) {
  const startTime = params.startTime || 0;
  const breakingPoint = params.breakingPoint || null;
  const firstFailure = params.firstFailure || null;
  const maxDeactivatedCount = params.maxDeactivatedCount || 0;

  return {
    totalRequests: data.metrics.iterations ? data.metrics.iterations.count : 0,
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
    testDuration: Math.round((Date.now() - startTime) / 1000),
    totalDeactivations: maxDeactivatedCount
  };
}
