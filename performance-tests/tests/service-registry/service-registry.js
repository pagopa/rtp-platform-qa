/**
 * k6 performance test script for stress testing the Service Registry endpoint.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, determineStage, getOptions, ActorCredentials } from '../../utils/utils.js';
import { serviceRegistryConfig } from '../../config/config.js';
import { createHandleSummary } from '../../utils/summary-utils.js';
import { createStandardMetrics } from '../../utils/metrics-utils.js';

const START_TIME = Date.now();
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/**
 * Defines test options based on the provided scenario name and test ID.
 */
export let options = getOptions(__ENV.SCENARIO, 'testServiceRegistry');

/**
 * Performs initial authentication as a service registry reader.
 *
 * @returns an object containing the access token to be used in test execution
 */
export function setup() {
  return setupAuth(ActorCredentials.SERVICE_REGISTRY_READER);
}

/**
 * Executes the main test logic by making a GET request to the service registry endpoint.
 *
 * @param {Object} data - the setup data containing the access token
 * @returns the HTTP response from the service registry
 */
export function testServiceRegistry(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;

  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: determineStage(elapsedSeconds)
  };

  currentRPS.add(1, tags);

  const headers = buildHeaders(data.access_token);
  const url = serviceRegistryConfig.baseUrl + '/service-providers';

  const start = Date.now();
  const res = http.get(url, { headers });
  const duration = Date.now() - start;

  responseTimeTrend.add(duration, tags);

  const successStatus = 200;

  if (res.status === successStatus) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
  }

  check(res, {
    'service registry: status is 200': (r) => r.status === successStatus
  });

  sleep(Math.random() * 2 + 0.5);
  return res;
}

/**
 * Provides a summary report configuration for this test run.
 */
export const handleSummary = createHandleSummary({
  START_TIME,
  testName: 'SERVICE REGISTRY STRESS TEST',
  countTag: 'fetchedServiceProvidersCount',
  reportPrefix: 'service-registry',
  VU_COUNT: 1000
});
