import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { analyzeTimeWindowsData, findBreakingPoint, findFirstFailure, getMaxTagCount, calculateOverallStats } from './metrics-utils.js';
import { generateTextReport } from './reporting-utils.js';

/**
 * Generates a detailed report on the test results.
 * Generic function that can be used by the handleSummary functions of different test cases.
 * 
 * @param {Object} params - Function parameters
 * @param {Object} params.data - Test data provided by k6
 * @param {number} params.startTime - Test start timestamp
 * @param {boolean} params.testCompleted - Flag indicating if the test was successfully completed
 * @param {number} params.vuCount - Number of virtual users used in the test
 * @param {string} params.testName - Name of the test (e.g. 'ACTIVATION STRESS TEST', 'DEACTIVATION STRESS TEST')
 * @param {string} params.countTag - Tag used for counting (e.g. 'activatedCount', 'deactivatedCount')
 * @param {string} params.reportPrefix - Prefix for report files (e.g. 'activation', 'deactivation')
 * @returns {Object} Object with file paths and their contents
 */
export function createTestSummary({ data, startTime, testCompleted, vuCount, testName, countTag, reportPrefix }) {
    console.log(`Generating enhanced summary for ${testName.toLowerCase()}...`);

    const timeWindowsAnalysis = analyzeTimeWindowsData(data);

    const breakingPoint = findBreakingPoint(timeWindowsAnalysis);
    const firstFailure = findFirstFailure(timeWindowsAnalysis);
    const maxCount = getMaxTagCount(data, countTag);

    if (breakingPoint) {
        breakingPoint[countTag] = maxCount;
    }
    if (firstFailure) {
        firstFailure[countTag] = maxCount;
    }

    const overallStats = calculateOverallStats(data, {
        startTime: startTime,
        breakingPoint: breakingPoint,
        firstFailure: firstFailure,
        [`max${countTag.charAt(0).toUpperCase() + countTag.slice(1)}`]: maxCount
    });

    const reportText = generateTextReport({
        testName: testName,
        testStatus: testCompleted ? "COMPLETED" : "INTERRUPTED",
        vuCount: vuCount,
        overallStats: overallStats,
        breakingPoint: breakingPoint,
        firstFailure: firstFailure,
        additionalContent: data.setupData && data.setupData.additionalReportContent ? data.setupData.additionalReportContent : ''
    });

    return {
        'stdout': textSummary(data, { indent: '  ', enableColors: true }),
        [`${reportPrefix}-stress-analysis.json`]: JSON.stringify({
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
        [`${reportPrefix}-report.txt`]: reportText
    };
}

/**
 * Helper function that creates a generator for handleSummary functions.
 * This allows you to define the handleSummary function more cleanly
 * in test files, reducing code duplication.
 * 
 * @param {Object} config - Base configuration for the report
 * @param {number} config.START_TIME - Test start timestamp
 * @param {string} config.testName - Name of the test (e.g. 'ACTIVATION STRESS TEST')
 * @param {string} config.countTag - Tag used for counting (e.g. 'activatedCount')
 * @param {string} config.reportPrefix - Prefix for report files (e.g. 'activation')
 * @param {number} config.VU_COUNT - Number of virtual users
 * @returns {function} The handleSummary function to export in the test file
 * 
 * @example
 * // In the test file:
 * export const handleSummary = createHandleSummary({
 *   START_TIME,
 *   testName: 'ACTIVATION STRESS TEST',
 *   countTag: 'activatedCount',
 *   reportPrefix: 'activation',
 *   VU_COUNT: VU_COUNT_SET
 * });
 */
export function createHandleSummary({ START_TIME, testName, countTag, reportPrefix, VU_COUNT }) {
    return function(data) {
        
        let testCompleted = false;
        
        if (typeof this.testCompleted !== 'undefined') {
            console.log(`Found testCompleted in global scope: ${this.testCompleted}`);
            testCompleted = this.testCompleted;
        } 
        else if (data.setupData && typeof data.setupData.testCompleted !== 'undefined') {
            console.log(`Found testCompleted in setupData: ${data.setupData.testCompleted}`);
            testCompleted = data.setupData.testCompleted;
        } 
        else if (data.setupData && typeof data.setupData.allCompleted !== 'undefined') {
            console.log(`Found allCompleted in setupData: ${data.setupData.allCompleted}`);
            testCompleted = data.setupData.allCompleted;
        }
        else if (data.metrics && data.metrics.failures && data.metrics.successes) {
            const failures = data.metrics.failures.values ? data.metrics.failures.values.count : 0;
            const successes = data.metrics.successes.values ? data.metrics.successes.values.count : 0;
            testCompleted = successes > 0 && (successes > failures * 2);
            console.log(`Inferred completion from metrics - successes: ${successes}, failures: ${failures}, testCompleted: ${testCompleted}`);
        }

        console.log(`Report generation - Test completed status: ${testCompleted}`);

        return createTestSummary({
            data,
            startTime: START_TIME,
            testCompleted,
            vuCount: VU_COUNT,
            testName,
            countTag,
            reportPrefix
        });
    };
}
