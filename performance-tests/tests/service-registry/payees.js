/**
 * k6 performance test script for stress testing the Payees endpoint.
 */

import http from 'k6/http';
import { check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { setupAuth, buildHeaders, determineStage, getOptions, ActorCredentials } from '../../utils/utils.js';
import { senderConfig } from '../../config/config.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';


const START_TIME = Date.now();
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * Defines test options based on scenario name and test ID.
 */
export let options = getOptions(__ENV.SCENARIO, 'testGetPayees');

/**
 * Performs authentication setup using CREDITOR_SERVICE_PROVIDER credentials.
 *
 * @returns an object containing the access token
 */
export function setup() {
  return setupAuth(ActorCredentials.PAGOPA_INTEGRATION_PAYEE_REGISTRY);
}

/**
 * Executes the main test logic:
 * - tracks metrics (RPS, response time)
 * - builds headers with auth, versioning, request ID
 * - sends GET request to /payees with pagination
 * - checks status, increments success/failure counters
 *
 * @param {Object} data - the setup data containing the access token
 * @returns {Response} The HTTP response object
 */
export function testGetPayees(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const page = __ENV.PAGE || 0;
  const size = __ENV.SIZE || 20;
  const url = `${senderConfig.sender_base}/payees/payees?page=${page}&size=${size}`;

  const headers = buildHeaders(data.access_token);
  headers['RequestId'] = uuidv4();
  headers['Version'] = 'v1';

  const start = Date.now();
  const res = http.get(url, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  if (res.status === 200) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
  }

  check(res, {
    'payees: status is 200': (r) => r.status === 200
  });

  return res;
}

/**
 * Provides summary report configuration for this test run.
 */
export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'PAYEES ENDPOINT STRESS TEST',
  countTag: 'fetchedPayeesCount',
  reportPrefix: 'payees',
  VU_COUNT: 150
});
