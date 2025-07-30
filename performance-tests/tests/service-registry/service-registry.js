import http from 'k6/http';
import { check, sleep } from 'k6';
import { setupAuth, buildHeaders, determineStage, doHandleSummary, getOptions, ActorCredentials } from '../../utils/utils.js';
import { serviceRegistryConfig } from '../../config/config.js';
import { Counter, Trend } from 'k6/metrics';

const START_TIME = Date.now();

const currentRPS = new Counter('current_rps');
const failureCounter = new Counter('failures');
const successCounter = new Counter('successes');
const responseTimeTrend = new Trend('response_time');


export let options = getOptions(__ENV.SCENARIO, 'testServiceRegistry');

export function setup() {
  return setupAuth(ActorCredentials.SERVICE_REGISTRY_READER);
}

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


export function handleSummary(data) {
  return doHandleSummary(data);
}