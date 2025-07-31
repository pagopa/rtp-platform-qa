/**
 * Generates a detailed textual report for the results of a stress test
 * 
 * @param {Object} params - Parameters for report generation
 * @param {string} params.testName - Name of the test
 * @param {string} params.testStatus - Status of the test (e.g. "COMPLETED", "ABORTED")
 * @param {number} params.vuCount - Number of virtual users used
 * @param {Object} params.overallStats - Overall test statistics
 * @param {Object} params.breakingPoint - Breaking point information (if any)
 * @param {Object} params.firstFailure - First failure information (if any)
 * @param {string} params.additionalContent - Additional content to include in the report
 * @returns {string} Formatted textual report
 */
export function generateTextReport({
  testName,
  testStatus,
  vuCount,
  overallStats,
  breakingPoint,
  firstFailure,
  additionalContent = ''
}) {
  return `
========== ${testName.toUpperCase()} REPORT ==========

TEST STATUS: ${testStatus}
VIRTUAL USERS: ${vuCount}

Overall Statistics:
- Total requests: ${overallStats.totalRequests}
- Successful operations: ${overallStats.successfulDeactivations}
- Failed operations: ${overallStats.failedDeactivations}
- Success rate: ${overallStats.successRate.toFixed(2)}%
- Failure rate: ${overallStats.failureRate.toFixed(2)}%
- Average response time: ${overallStats.avgResponseTime.toFixed(2)} ms
- P95 response time: ${overallStats.p95ResponseTime.toFixed(2)} ms
- Total test duration: ${overallStats.testDuration} seconds
- Total operations: ${overallStats.totalDeactivations}

${breakingPoint ? `
BREAKING POINT IDENTIFIED:
- After ${breakingPoint.deactivatedCount} operations
- At ${breakingPoint.secondsFromStart} seconds from test start
- With failure rate: ${breakingPoint.failureRate.toFixed(2)}%
- Average response time: ${breakingPoint.avgResponseTime.toFixed(2)} ms` : 
'NO BREAKING POINT IDENTIFIED during the test'}

${firstFailure ? `
FIRST FAILURE:
- After ${firstFailure.deactivatedCount} operations
- At ${firstFailure.secondsFromStart} seconds from test start
- Number of failures: ${firstFailure.failures}` : 
'NO FAILURE occurred during the test'}

${additionalContent}
==========================================================
`;
}

/**
 * Generates a report for virtual user statistics
 * 
 * @param {Array} vuStats - Array of statistics for each virtual user
 * @returns {string} Formatted text with VU statistics
 */
export function generateVuStatsText(vuStats) {
  let vuStatsText = 'STATISTICS FOR VIRTUAL USER:\n';
  vuStats.forEach(stat => {
    vuStatsText += `- VU #${stat.vu}: ${stat.deactivated}/${stat.total} (${stat.percentage}%)\n`;
  });
  return vuStatsText;
}

/**
 * Generates additional information from the teardown for the report
 * 
 * @param {Object} finalState - Final state of the test
 * @param {string} vuStatsText - Text with the statistics for VU
 * @returns {string} Formatted text with the additional information
 */
export function generateTeardownInfo(finalState, vuStatsText) {
  return `
ADDITIONAL INFORMATION FROM TEARDOWN:
- Test completed: ${finalState.testCompleted ? "Yes" : "No"}
- Total operations: ${finalState.totalActivations}
- Completed operations: ${finalState.deactivatedCount} (${(finalState.deactivatedCount / finalState.totalActivations * 100).toFixed(1)}%)
- Duration (seconds): ${finalState.testDuration}

${vuStatsText}
`;
}
