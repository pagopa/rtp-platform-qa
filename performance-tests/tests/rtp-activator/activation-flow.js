import http from \x27k6/http\x27;
import { check, sleep } from \x27k6\x27;
import { uuidv4 } from \x27https://jslib.k6.io/k6-utils/1.4.0/index.js\x27;
import {
  setupAuth,
  randomFiscalCode,
  buildHeaders,
  endpoints,
  getStageLabel,
  getOptions,
  describeScenarioVUs,
  ActorCredentials
} from \x27../../utils/utils.js\x27;
import { createHandleSummary } from \x27../../utils/summary-utils.js\x27;
import { createStandardMetrics } from \x27../../utils/metrics-utils.js\x27;
import { createActivationTeardown } from \x27../../utils/teardown-utils.js\x27;

/**
 * @file Activation Flow Stress Test (k6)
 * @description
 * Complete activation lifecycle stress test:
 * 1. POST /activations?toPublish=true (creates activation)
 * 2. GET /activations/{activationId} (retrieves activation details)
 * 3. DELETE /activations/{activationId} (deactivates activation)
 *
 * ## Inputs
 * - Environment variables:
 *   - `DEBTOR_SERVICE_PROVIDER_ID` (required): Debtor Service Provider identifier used in payloads.
 *   - `SCENARIO` (string, optional, default: \x27custom\x27): Load profile to execute.
 *   - `VU_COUNT_SET` (number, optional, default: 10): Number of Virtual Users.
 *   - `ITERATIONS` (number, optional, default: 1000): Total iterations across all VUs (for custom scenario).
 *   - `SLEEP_ITER` (number, seconds, optional, default: 0): Sleep time between iterations.
 */

/** Run start timestamp (ms). */
const START_TIME = Date.now();

/** Debtor Service Provider ID from environment (required). */
const DEBTOR_SERVICE_PROVIDER_ID = String(__ENV.DEBTOR_SERVICE_PROVIDER_ID || \x27\x27);

if (!DEBTOR_SERVICE_PROVIDER_ID) {
  throw new Error(\x27❌ DEBTOR_SERVICE_PROVIDER_ID cannot be null or undefined\x27);
}

/** Number of virtual users. */
const VU_COUNT = Number(__ENV.VU_COUNT_SET) || 10;

/** Total shared iterations for the scenario. */
const ITERATIONS = Number(__ENV.ITERATIONS) || 1000;

/** Optional per-iteration sleep (seconds). */
const SLEEP_ITER = Number(__ENV.SLEEP_ITER) || 0;

/** Load profile to use. */
const SCENARIO = __ENV.SCENARIO || \x27custom\x27;

/** Scenario names backed by progressiveOptions in utils.js */
const PREDEFINED_SCENARIOS = [
  \x27stress_test\x27, \x27soak_test\x27, \x27spike_test\x27,
  \x27stress_test_fixed_user\x27, \x27soak_test_fixed_user\x27, \x27spike_test_fixed_user\x27
];

if (SCENARIO !== \x27custom\x27 && !PREDEFINED_SCENARIOS.includes(SCENARIO)) {
  throw new Error(
    `❌ Unknown SCENARIO \"${SCENARIO}\". Expected one of: \x27custom\x27, ${PREDEFINED_SCENARIOS.map((s) => `\x27${s}\x27`).join(\x27, \x27)}`
  );
}

/** Custom performance metrics */
const { currentRPS, failureCounter, successCounter, responseTimeTrend } = createStandardMetrics();

/** Mutable ref object for test completion state. */
const testCompletedRef = { value: false };

/**
 * k6 execution options.
 * @type {import(\x27k6/options\x27).Options}
 */
export let options = PREDEFINED_SCENARIOS.includes(SCENARIO)
  ? {
      ...getOptions(SCENARIO, \x27activate\x27),
      setupTimeout: \x275m\x27
    }
  : {
      ...getOptions(\x27stress_test_fixed_user\x27, \x27activate\x27),
      setupTimeout: \x275m\x27,
      scenarios: {
        stress_test_fixed_user: {
          executor: \x27shared-iterations\x27,
          vus: VU_COUNT,
          iterations: ITERATIONS,
          maxDuration: \x2730m\x27,
          gracefulStop: \x2730m\x27,
          exec: \x27activate\x27
        }
      }
    };

/**
 * k6 setup lifecycle function.
 * Authenticates as DEBTOR_SERVICE_PROVIDER.
 */
export function setup() {
  return setupAuth(ActorCredentials.DEBTOR_SERVICE_PROVIDER);
}

/**
 * Complete activation lifecycle worker executed per iteration.
 */
export function activate(data) {
  const elapsedSeconds = (Date.now() - START_TIME) / 1000;
  const tags = {
    timeWindow: Math.floor(elapsedSeconds / 10) * 10,
    stage: getStageLabel(SCENARIO, elapsedSeconds),
    vu: String(__VU)
  };

  currentRPS.add(1, tags);

  const headers = {
    ...buildHeaders(data.access_token),
    \x27Content-Type\x27: \x27application/json\x27,
    \x27Version\x27: \x27v1\x27,
    \x27RequestId\x27: uuidv4()
  };

  const debtorFiscalCode = randomFiscalCode();
  const activationPayload = {
    payer: {
      fiscalCode: debtorFiscalCode,
      rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
    }
  };

  const start = Date.now();
  let stepSuccess = true;

  // 1. POST /activations?toPublish=true (create activation)
  const actRes = http.post(
    `${endpoints.activations}?toPublish=true`,
    JSON.stringify(activationPayload),
    { headers }
  );

  const isActOk = actRes.status === 201;
  check(actRes, { \x27activation: status is 201\x27: () => isActOk });

  if (!isActOk) {
    stepSuccess = false;
    console.error(`❌ VU #${__VU}: Activation failed — Status ${actRes.status}, Body: ${actRes.body}`);
  } else {
    let activationId = null;
    if (actRes.headers[\x27Location\x27]) {
      activationId = actRes.headers[\x27Location\x27].split(\x27/\x27).pop();
    } else if (actRes.json && actRes.json(\x27activationId\x27)) {
      activationId = actRes.json(\x27activationId\x27);
    } else {
      try {
        const body = JSON.parse(actRes.body);
        activationId = body.activationId || body.id || null;
      } catch (e) {
        activationId = null;
      }
    }

    if (activationId) {
      // 2. GET /activations/{activationId} (verify retrieval)
      const getByIdRes = http.get(
        `${endpoints.activations}/${activationId}`,
        { headers }
      );
      const isGetOk = getByIdRes.status === 200;
      check(getByIdRes, { \x27get by id: status is 200\x27: () => isGetOk });

      if (!isGetOk) {
        stepSuccess = false;
        console.error(`❌ VU #${__VU}: Get activation by ID failed for ${activationId}: Status ${getByIdRes.status}`);
      }

      // 3. DELETE /activations/{activationId} (deactivate)
      const deactRes = http.del(
        `${endpoints.activations}/${activationId}`,
        null,
        { headers }
      );
      const isDeactOk = deactRes.status === 204;
      check(deactRes, { \x27deactivation: status is 204\x27: () => isDeactOk });

      if (!isDeactOk) {
        stepSuccess = false;
        console.error(`❌ VU #${__VU}: Deactivation failed for ${activationId}: Status ${deactRes.status}`);
      }
    } else {
      stepSuccess = false;
      console.error(`❌ VU #${__VU}: Activation succeeded but failed to extract activationId from response`);
    }
  }

  const duration = Date.now() - start;
  responseTimeTrend.add(duration, tags);

  if (stepSuccess) {
    successCounter.add(1, tags);
  } else {
    failureCounter.add(1, tags);
  }

  if (SLEEP_ITER > 0) {
    sleep(SLEEP_ITER);
  }

  return actRes;
}

/**
 * k6 teardown export.
 */
export const teardown = createActivationTeardown({
  START_TIME,
  VU_COUNT,
  testCompletedRef
});

/**
 * k6 handleSummary export.
 */
export const handleSummary = (opts) => {
  return createHandleSummary({
    START_TIME,
    testName: \x27ACTIVATION FLOW STRESS TEST\x27,
    countTag: \x27requestCount\x27,
    reportPrefix: \x27activation-flow\x27,
    VU_COUNT: describeScenarioVUs(SCENARIO, VU_COUNT),
    testCompletedRef,
    scenarioConfig: options.scenarios ? options.scenarios[SCENARIO] : undefined
  })(opts);
};
