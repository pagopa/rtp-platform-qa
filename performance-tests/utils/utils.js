import http from 'k6/http';
import {activationConfig, callbackConfig, senderConfig} from '../config/config.js';

export const config = activationConfig;
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';


export const ActorCredentials = {
  DEBTOR_SERVICE_PROVIDER: 'DEBTOR_SERVICE_PROVIDER',
  DEBTOR_SERVICE_PROVIDER_FAKESP: "DEBTOR_SERVICE_PROVIDER_FAKESP",
  CREDITOR_SERVICE_PROVIDER: 'CREDITOR_SERVICE_PROVIDER',
  SERVICE_REGISTRY_READER: 'SERVICE_REGISTRY_READER',
  PAGOPA_INTEGRATION_PAYEE_REGISTRY: 'PAGOPA_INTEGRATION_PAYEE_REGISTRY',
  RTP_CONSUMER: "RTP_CONSUMER"
};


const ACTOR_CREDENTIALS_MAP = {
  [ActorCredentials.DEBTOR_SERVICE_PROVIDER]: {
    clientId: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
    clientSecret: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET,
  },
  [ActorCredentials.DEBTOR_SERVICE_PROVIDER_FAKESP]: {
    clientId: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_ID_FAKESP,
    clientSecret: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET_FAKESP,
  },
  [ActorCredentials.CREDITOR_SERVICE_PROVIDER]: {
    clientId: __ENV.CREDITOR_SERVICE_PROVIDER_CLIENT_ID,
    clientSecret: __ENV.CREDITOR_SERVICE_PROVIDER_CLIENT_SECRET,
  },
  [ActorCredentials.SERVICE_REGISTRY_READER]: {
    clientId: __ENV.SERVICE_REGISTRY_READER_CLIENT_ID,
    clientSecret: __ENV.SERVICE_REGISTRY_READER_CLIENT_SECRET,
  },
  [ActorCredentials.PAGOPA_INTEGRATION_PAYEE_REGISTRY]: {
    clientId: __ENV.PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_ID,
    clientSecret: __ENV.PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_SECRET,
  },
  [ActorCredentials.RTP_CONSUMER]: {
    clientId: __ENV.RTP_CONSUMER_CLIENT_ID,
    clientSecret: __ENV.RTP_CONSUMER_CLIENT_SECRET,
  }
};


/**
 * Gets a valid access token using client credentials authentication.
 *
 * @param {string} access_token_url - OAuth token endpoint URL
 * @param {string} client_id - Client ID for authentication
 * @param {string} client_secret - Client secret for authentication
 * @returns {string} Access token for API authorization
 * @throws {Error} If authentication fails
 */
export function getValidAccessToken(access_token_url, client_id, client_secret) {
    const payload = {
        client_id: client_id,
        client_secret: client_secret,
        grant_type: 'client_credentials',
    };
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
    const res = http.post(access_token_url, payload, { headers: headers, responseType: "text", discardResponseBodies: false });

    if (res.status !== 200) {
        throw new Error(`Failed to get access token. Status code: ${res.status}`);
    }

    return res.json().access_token;
}


function retrieveActorClientCredentials(actor) {
	const credentials = ACTOR_CREDENTIALS_MAP[actor];
	if (!credentials) {
		console.debug("Unrecognized ActorCredentials: " + actor);
		return { clientId: null, clientSecret: null };
	}
	return credentials;
}


/**
 * Sets up authentication for API requests using environment variables related to given actor.
 *
 * @param {string} actor - The actor to fetch credentials for
 * @returns {Object} Object containing the access_token
 * @throws {Error} If required environment variables are missing
 */
export function setupAuth(actor = ActorCredentials.DEBTOR_SERVICE_PROVIDER) {
	let {clientId, clientSecret} = retrieveActorClientCredentials(actor);

    if (!clientId || !clientSecret) {
        console.error('⚠️ Missing client credentials');
        throw new Error('Client credentials are not set');
    }
    const token = getValidAccessToken(
        config.access_token_url,
        clientId,
        clientSecret
    );

    return { access_token: token };
}

/**
 * Generates a random fiscal code for testing purposes.
 * Creates a basic numeric fiscal code with 11 digits.
 *
 * @returns {string} Random fiscal code as a zero-padded string
 */
export function randomFiscalCode() {
    return Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
}

/**
 * Generates a random notice number for testing purposes.
 * Creates a basic numeric notice numeber code with 18 digits.
 *
 * @returns {string} Random notice number as a zero-padded string
 */
export function randomNoticeNumber() {
    return Math.floor(Math.random() * 1e18).toString().padStart(18, '0');
}

/**
 * Remove dashes from a UUID string.
 *
 * @param {string} uuid - The UUID string in canonical format (with dashes).
 * @returns {string} - The UUID string with all dashes removed.
 */
export function replaceUuidWithoutDashes(uuid) {
    if (!uuid) {
        console.error("replaceUuidWithoutDashes got invalid uuid:", uuid);
        return "";
    }
    return String(uuid).replace(/-/g, '');
}

/**
 * Common options used across all test types.
 * These settings configure the metrics collection and tagging behavior.
 */
export const commonOptions = {
  summaryTrendStats: ['avg','min','med','max','p(90)','p(95)','p(99)'],
  systemTags: ['status','method','url','name','group','check','error','scenario'],
};

/**
/**
 * Builds a staircase of ramp stages from `startRate` to `peakRate`, split into
 * `steps` equal increments, each held for `stepDuration`. Used by `stress_test`.
 *
 * @param {number} startRate - Starting request rate (req/s).
 * @param {number} peakRate - Target/peak request rate (req/s).
 * @param {number} steps - Number of staircase steps.
 * @param {string} stepDuration - k6 duration string held at each step (e.g. '30s').
 * @returns {Array<{target: number, duration: string}>} k6 ramping-arrival-rate stages.
 */
function buildStaircaseStages(startRate, peakRate, steps, stepDuration) {
  const stages = [];
  for (let i = 1; i <= steps; i++) {
    const target = Math.round(startRate + (peakRate - startRate) * i / steps);
    stages.push({ target, duration: '1s' });
    stages.push({ target, duration: stepDuration });
  }
  return stages;
}

/**
 * Builds the `stress_test` scenario: a staircase ramp from a start rate up to
 * a peak rate, meant to find the system's breaking point.
 *
 * Configurable via env vars (all optional, defaults shown):
 * - `RAMP_START_RATE` (default 10): starting req/s.
 * - `RAMP_PEAK_RATE` (default 5000): peak req/s to ramp up to.
 * - `RAMP_STEPS` (default 10): number of staircase steps between start and peak.
 * - `RAMP_STEP_DURATION` (default '30s'): how long each step is held.
 * - `RAMP_PRE_ALLOCATED_VUS` / `RAMP_MAX_VUS` (optional): override the k6 VU
 *   pool sizing; if omitted, sized automatically from `RAMP_PEAK_RATE`.
 *   `maxVUs` is always clamped to be >= `preAllocatedVUs`.
 *
 * BREAKING CHANGE vs. the previous hardcoded `stress_test`: when no `RAMP_*`
 * env vars are set (e.g. running the script locally without `-e` flags), the
 * default shape has 10 staircase levels (20 k6 stages: a 1s ramp plus a 30s
 * hold per level), ending at 5000 req/s with no recovery ramp-down. The legacy
 * default had 17 stages (holds at each level) and ramped back down to 50
 * req/s at the end. This is intentional: the scenario is now meant to be
 * driven by the ADO pipeline parameters (see `srtp-deploy-aks/.devops/k6-stress-test.yml`)
 * rather than by a fixed hardcoded shape. If you need the old recovery-ramp
 * behavior for a local run, set `RAMP_*` env vars explicitly to replicate it.
 *
 * @returns {Object} k6 `ramping-arrival-rate` scenario definition.
 */
function buildStressTestScenario() {
  const startRate = Number(__ENV.RAMP_START_RATE) || 10;
  const peakRate = Number(__ENV.RAMP_PEAK_RATE) || 5000;
  const steps = Number(__ENV.RAMP_STEPS) || 10;
  const stepDuration = __ENV.RAMP_STEP_DURATION || '30s';
  const preAllocatedVUs = Number(__ENV.RAMP_PRE_ALLOCATED_VUS) || Math.max(10, Math.round(peakRate / 25));
  const maxVUs = Math.max(preAllocatedVUs, Number(__ENV.RAMP_MAX_VUS) || peakRate);

  return {
    executor: 'ramping-arrival-rate',
    startRate,
    timeUnit: '1s',
    preAllocatedVUs,
    maxVUs,
    exec: 'activate',
    stages: buildStaircaseStages(startRate, peakRate, steps, stepDuration)
  };
}

/**
 * Builds the `soak_test` scenario: a constant, moderate request rate held for
 * an extended period, meant to surface slow leaks/degradation over time.
 *
 * Configurable via env vars (all optional, defaults shown):
 * - `SOAK_RATE` (default 20): constant req/s.
 * - `SOAK_DURATION` (default '5m'): total test duration.
 * - `SOAK_PRE_ALLOCATED_VUS` / `SOAK_MAX_VUS` (optional): override the k6 VU
 *   pool sizing; if omitted, sized automatically from `SOAK_RATE`.
 *   `maxVUs` is always clamped to be >= `preAllocatedVUs`.
 *
 * @returns {Object} k6 `constant-arrival-rate` scenario definition.
 */
function buildSoakTestScenario() {
  const rate = Number(__ENV.SOAK_RATE) || 20;
  const duration = __ENV.SOAK_DURATION || '5m';
  const preAllocatedVUs = Number(__ENV.SOAK_PRE_ALLOCATED_VUS) || Math.max(10, Math.round(rate * 2.5));
  const maxVUs = Math.max(preAllocatedVUs, Number(__ENV.SOAK_MAX_VUS) || rate * 10);

  return {
    executor: 'constant-arrival-rate',
    rate,
    timeUnit: '1s',
    duration,
    preAllocatedVUs,
    maxVUs,
    exec: 'activate'
  };
}

/**
 * Builds the `spike_test` scenario: a baseline rate, a sudden burst to a peak
 * rate, held briefly, then back to baseline — meant to test recovery behavior.
 *
 * Configurable via env vars (all optional, defaults shown):
 * - `SPIKE_BASE_RATE` (default 10): baseline req/s before/after the spike.
 * - `SPIKE_PEAK_RATE` (default 300): req/s reached during the spike.
 * - `SPIKE_RAMP_DURATION` (default '10s'): time to ramp up to / down from the peak.
 * - `SPIKE_HOLD_DURATION` (default '30s'): time held at the peak rate.
 * - `SPIKE_BASE_HOLD_DURATION` (default '10s'): time held at baseline before the spike.
 * - `SPIKE_PRE_ALLOCATED_VUS` / `SPIKE_MAX_VUS` (optional): override the k6 VU
 *   pool sizing; if omitted, sized automatically from `SPIKE_PEAK_RATE`.
 *   `maxVUs` is always clamped to be >= `preAllocatedVUs`.
 *
 * @returns {Object} k6 `ramping-arrival-rate` scenario definition.
 */
function buildSpikeTestScenario() {
  const baseRate = Number(__ENV.SPIKE_BASE_RATE) || 10;
  const peakRate = Number(__ENV.SPIKE_PEAK_RATE) || 300;
  const rampDuration = __ENV.SPIKE_RAMP_DURATION || '10s';
  const holdDuration = __ENV.SPIKE_HOLD_DURATION || '30s';
  const baseHoldDuration = __ENV.SPIKE_BASE_HOLD_DURATION || '10s';
  const preAllocatedVUs = Number(__ENV.SPIKE_PRE_ALLOCATED_VUS) || Math.max(10, Math.round(peakRate / 15));
  const maxVUs = Math.max(preAllocatedVUs, Number(__ENV.SPIKE_MAX_VUS) || peakRate);

  return {
    executor: 'ramping-arrival-rate',
    startRate: baseRate,
    timeUnit: '1s',
    preAllocatedVUs,
    maxVUs,
    exec: 'activate',
    stages: [
      { target: baseRate, duration: baseHoldDuration },
      { target: peakRate, duration: rampDuration },
      { target: peakRate, duration: holdDuration },
      { target: baseRate, duration: rampDuration }
    ]
  };
}

/**
 * Progressive test options with different test scenarios.
 * Contains predefined scenarios for different load testing strategies:
 * - stress_test: Gradually increases load to find system breaking points
 * - soak_test: Maintains constant moderate load for extended periods
 * - spike_test: Creates sudden burst of traffic to test recovery
 *
 * Each scenario's shape/rates/durations are configurable via env vars (see
 * `buildStressTestScenario`/`buildSoakTestScenario`/`buildSpikeTestScenario`
 * above for the accepted env vars and their defaults) so they can be tuned
 * from the ADO pipeline parameters without code changes.
 */
export const progressiveOptions = {
  ...commonOptions,
  scenarios: {
    stress_test: buildStressTestScenario(),
    soak_test: buildSoakTestScenario(),
    spike_test: buildSpikeTestScenario()
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    failures: [],
    successes: [],
    current_rps: ['rate>0'],
    checks: []
  }
};

/**
 * Fixed virtual user count scenario variants.
 * These scenarios use constant number of VUs rather than arrival rate.
 */
progressiveOptions.scenarios.stress_test_fixed_user = {
  executor: 'constant-vus',
  vus: 100,
  duration: '1m',
  exec: 'activate'
};
progressiveOptions.scenarios.soak_test_fixed_user = {
  executor: 'constant-vus',
  vus: 100,
  duration: progressiveOptions.scenarios.soak_test.duration,
  exec: 'activate'
};
progressiveOptions.scenarios.spike_test_fixed_user = {
  executor: 'constant-vus',
  vus: 100,
  duration: '1m',
  exec: 'activate'
};

/**
 * Builds standard headers for API requests.
 * Includes authorization, content type, version, and request ID.
 *
 * @param {string} token - Access token for Bearer authentication
 * @returns {Object} Headers object for HTTP requests
 */
export function buildHeaders(token) {
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'Version': 'v1',
    'RequestId': uuidv4()
  };
}

/**
 * Legacy stage classifier: maps elapsed time to named stages using hardcoded
 * time thresholds. Kept only as a fallback for the `custom`/`shared-iterations`
 * mode, which has no rate/VU ramp to derive a stage from.
 *
 * NOTE: these thresholds do NOT match the current `stress_test`/`soak_test`/
 * `spike_test` scenario definitions above (durations have since changed) — use
 * `getStageLabel()` instead for any of the `PREDEFINED_SCENARIOS`, which derives
 * the stage from the actual scenario config instead of a hardcoded guess.
 *
 * @param {number} sec - Elapsed seconds since test start
 * @returns {string} Current stage name
 */
export function determineStage(sec) {
  if (sec <= 30) return 'ramp-50';
  if (sec <= 60) return 'stable-50';
  if (sec <= 90) return 'ramp-100';
  if (sec <= 120) return 'stable-100';
  if (sec <= 150) return 'ramp-250';
  if (sec <= 180) return 'stable-250';
  if (sec <= 210) return 'ramp-500';
  if (sec <= 240) return 'stable-500';
  if (sec <= 270) return 'ramp-1000';
  if (sec <= 300) return 'stable-1000';
  if (sec <= 330) return 'ramp-2500';
  if (sec <= 360) return 'stable-2500';
  if (sec <= 390) return 'ramp-5000';
  if (sec <= 450) return 'stable-5000';
  if (sec <= 480) return 'recovery-1000';
  if (sec <= 510) return 'recovery-250';
  return 'recovery-50';
}

/**
 * Parses a k6-style duration string (e.g. '30s', '1m', '1m30s') into seconds.
 *
 * @param {string} duration - Duration string using ms/s/m/h unit suffixes.
 * @returns {number} Total duration in seconds.
 */
export function parseDurationToSeconds(duration) {
  const matches = String(duration).matchAll(/(\d+)(ms|s|m|h)/g);
  const unitSeconds = { ms: 0.001, s: 1, m: 60, h: 3600 };
  let total = 0;
  for (const [, amount, unit] of matches) {
    total += Number(amount) * unitSeconds[unit];
  }
  return total;
}

/**
 * Computes the total expected iterations and total planned duration (ms) for an
 * arrival-rate scenario (`constant-arrival-rate` / `ramping-arrival-rate`), purely
 * from its static configuration (rate/stages/duration) — no dependency on actual
 * success/failure counts. Used to determine whether a run reached its full
 * planned schedule, regardless of how many requests failed along the way.
 *
 * For `ramping-arrival-rate`, the rate varies linearly within each stage, so the
 * expected iterations for that stage are the area under the ramp (trapezoidal:
 * `(previousRate + stageTarget) / 2 * stageDurationSec`).
 *
 * @param {Object} scenarioConfig - A resolved k6 scenario definition (as returned
 *   by `buildStressTestScenario`/`buildSoakTestScenario`/`buildSpikeTestScenario`
 *   or any `constant-arrival-rate`/`ramping-arrival-rate` scenario object).
 * @returns {{expectedIterations: number, expectedDurationMs: number} | null}
 *   `null` if `scenarioConfig` is not an arrival-rate executor (e.g. `shared-iterations`,
 *   `constant-vus`), for which this computation doesn't apply.
 */
export function computeExpectedArrivalRateSchedule(scenarioConfig) {
  if (!scenarioConfig) return null;

  const timeUnitSec = parseDurationToSeconds(scenarioConfig.timeUnit || '1s') || 1;

  if (scenarioConfig.executor === 'constant-arrival-rate') {
    const durationSec = parseDurationToSeconds(scenarioConfig.duration);
    return {
      expectedIterations: (scenarioConfig.rate * durationSec) / timeUnitSec,
      expectedDurationMs: durationSec * 1000
    };
  }

  if (scenarioConfig.executor === 'ramping-arrival-rate' && Array.isArray(scenarioConfig.stages)) {
    let previousRate = scenarioConfig.startRate || 0;
    let expectedIterations = 0;
    let expectedDurationMs = 0;

    for (const stage of scenarioConfig.stages) {
      const stageDurationSec = parseDurationToSeconds(stage.duration);
      const avgRate = (previousRate + stage.target) / 2;
      expectedIterations += (avgRate * stageDurationSec) / timeUnitSec;
      expectedDurationMs += stageDurationSec * 1000;
      previousRate = stage.target;
    }

    return { expectedIterations, expectedDurationMs };
  }

  return null;
}

/**
 * Determines whether an arrival-rate scenario (`stress_test`/`soak_test`/`spike_test`)
 * ran to completion, using two independent, failure-rate-agnostic signals instead of
 * a success/failure ratio heuristic (which incorrectly treats a high failure rate as
 * "interrupted", even though a high failure rate is often the *expected outcome* of a
 * stress/soak/spike test):
 *
 * 1. **Duration** (lower-bound check): `data.state.testRunDurationMs` is the actual
 *    wall-clock time k6 ran for. If it's meaningfully less than the planned total
 *    stage/duration time, the run was cut short.
 * 2. **Executed iterations** (primary check, robust to *HTTP* failure rate — but
 *    NOT to VU starvation): k6's built-in `iterations` metric counts every
 *    iteration k6 actually *started*, regardless of whether the underlying HTTP
 *    request succeeded or failed. Comparing this against the analytically-computed
 *    expected iteration count (see `computeExpectedArrivalRateSchedule`) tells us
 *    whether the full planned schedule ran, independent of the error rate.
 *    `dropped_iterations` (arrivals k6 could NOT start because no VU was free) are
 *    deliberately NOT credited here — they represent a load shortfall (VU pool
 *    starved by a saturated/slow backend), not executed work, so a run with
 *    significant drops correctly falls short of `expectedIterations` and is
 *    reported as `INTERRUPTED` rather than being masked as `COMPLETED`.
 *
 * A small tolerance (`maxVUs` + 2% of expected iterations) accounts for iterations
 * still in-flight when the run ends and for scheduling rounding.
 *
 * @param {Object} data - The `data` object k6 passes to `handleSummary`.
 * @param {Object} scenarioConfig - The resolved scenario definition (see
 *   `computeExpectedArrivalRateSchedule`).
 * @returns {{status: 'COMPLETED'|'INTERRUPTED'|'UNKNOWN', reason: string}}
 */
export function evaluateArrivalRateCompletion(data, scenarioConfig) {
  const schedule = computeExpectedArrivalRateSchedule(scenarioConfig);
  if (!schedule) {
    return { status: 'UNKNOWN', reason: 'Scenario is not an arrival-rate executor; cannot evaluate schedule completion.' };
  }

  const actualDurationMs = data && data.state ? data.state.testRunDurationMs : undefined;
  if (typeof actualDurationMs === 'number' && actualDurationMs < schedule.expectedDurationMs * 0.95) {
    return {
      status: 'INTERRUPTED',
      reason: `Actual run duration (${Math.round(actualDurationMs)}ms) is well below the planned duration (${Math.round(schedule.expectedDurationMs)}ms).`
    };
  }

  const executedIterations = data?.metrics?.iterations?.values?.count ?? 0;
  const droppedIterations = data?.metrics?.dropped_iterations?.values?.count ?? 0;

  const maxVUs = scenarioConfig.maxVUs || scenarioConfig.preAllocatedVUs || 10;
  const tolerance = maxVUs + Math.ceil(schedule.expectedIterations * 0.02);

  if (executedIterations < schedule.expectedIterations - tolerance) {
    return {
      status: 'INTERRUPTED',
      reason: `Only ${executedIterations} of ~${Math.round(schedule.expectedIterations)} expected iterations were executed` +
        (droppedIterations > 0 ? ` (${droppedIterations} additionally dropped due to VU starvation)` : '') +
        ` (tolerance ${tolerance}).`
    };
  }

  return {
    status: 'COMPLETED',
    reason: `Ran ${executedIterations} of ~${Math.round(schedule.expectedIterations)} expected iterations, full planned duration reached` +
      (droppedIterations > 0 ? ` (${droppedIterations} dropped due to VU starvation, within tolerance)` : '') + '.'
  };
}

/**
 * Determines the current stage label for one of the `PREDEFINED_SCENARIOS`,
 * derived directly from that scenario's actual `stages`/`rate`/`vus` config
 * (unlike the legacy `determineStage()`, this always matches reality since it
 * doesn't rely on hardcoded time thresholds).
 *
 * @param {string} scenarioName - Scenario name (key in `progressiveOptions.scenarios`),
 *   or any other value for the `custom`/`shared-iterations` fallback.
 * @param {number} elapsedSeconds - Elapsed seconds since test start.
 * @returns {string} Current stage label.
 */
export function getStageLabel(scenarioName, elapsedSeconds) {
  const scenario = progressiveOptions.scenarios[scenarioName];

  if (!scenario) {
    return determineStage(elapsedSeconds);
  }

  if (Array.isArray(scenario.stages)) {
    let cumulative = 0;
    for (const stage of scenario.stages) {
      cumulative += parseDurationToSeconds(stage.duration);
      if (elapsedSeconds <= cumulative) {
        return `rate-${stage.target}`;
      }
    }
    const lastStage = scenario.stages[scenario.stages.length - 1];
    return `rate-${lastStage.target}`;
  }

  if (scenario.executor === 'constant-arrival-rate') {
    return `rate-${scenario.rate}`;
  }

  if (scenario.executor === 'constant-vus') {
    return `vus-${scenario.vus}`;
  }

  return 'n/a';
}

/**
 * List of all possible test stages in order.
 * Used for reporting and analysis of test results.
 */
export const stages = [
  'ramp-50', 'stable-50', 'ramp-100', 'stable-100', 'ramp-250', 'stable-250',
  'ramp-500', 'stable-500', 'ramp-1000', 'stable-1000', 'ramp-2500', 'stable-2500',
  'ramp-5000', 'stable-5000', 'recovery-1000', 'recovery-250', 'recovery-50'
];

/**
 * API endpoints used in the tests.
 * Centralized configuration of URLs to avoid duplication across test scripts.
 */
export const endpoints = {
  activations: `${activationConfig.activation_base}/activations`,
  deactivations: `${activationConfig.activation_base}/activations`,
  takeover: `${activationConfig.activation_base}/activations/takeover`,
  sendRtp: `${senderConfig.sender_base}/rtps`,
  callbackSend : `${callbackConfig.callback_base}/cb/send`,
  callbackCancel: `${callbackConfig.callback_base}/cb/cancel`,
  getByFiscalCode: `${activationConfig.activation_base}/activations/payer`,
  gpdMessage: `${senderConfig.sender_base}/gpd/message`,
  deliveryStatus: `${senderConfig.sender_base}/rtps/delivery-status`,
};

/**
 * Builds test options based on scenario name and execution function.
 * Creates a deep copy of the selected scenario to avoid reference issues.
 *
 * @param {string} scenarioName - Name of the scenario to use (must exist in progressiveOptions.scenarios)
 * @param {string} execFunction - Name of the function to execute for this scenario
 * @returns {Object} Complete k6 options object with the selected scenario
 */
export function getOptions(scenarioName, execFunction) {
  const scenarioKey = scenarioName in progressiveOptions.scenarios
    ? scenarioName
    : 'stress_test';

  const scenario = JSON.parse(JSON.stringify(progressiveOptions.scenarios[scenarioKey]));
  if (execFunction) {
    scenario.exec = execFunction;
  }

  return {
    summaryTrendStats: progressiveOptions.summaryTrendStats,
    systemTags: progressiveOptions.systemTags,
    scenarios: {
      [scenarioKey]: scenario
    },
    thresholds: progressiveOptions.thresholds
  };
}

/**
 * Builds a human-readable description of the VU allocation for a given
 * predefined scenario, for use in end-of-test reports. Arrival-rate executors
 * (`stress_test`, `soak_test`, `spike_test`) don't run a fixed number of VUs
 * (k6 allocates VUs dynamically between `preAllocatedVUs` and `maxVUs` to hit
 * the target rate), so reporting a single static VU count for them would be
 * misleading; `constant-vus`/`shared-iterations` executors do use a fixed count.
 *
 * @param {string} scenarioName - One of `PREDEFINED_SCENARIOS`, or any other
 *   value (treated as the `custom` shared-iterations case).
 * @param {number} fallbackVuCount - VU count to report for the `custom` case
 *   (i.e. the `VU_COUNT_SET` env var driving the `shared-iterations` executor).
 * @returns {string} Human-readable VU allocation description.
 */
export function describeScenarioVUs(scenarioName, fallbackVuCount) {
  const scenario = progressiveOptions.scenarios[scenarioName];

  if (!scenario) {
    return `${fallbackVuCount} (custom, shared-iterations)`;
  }

  if (scenario.executor === 'constant-vus') {
    return `${scenario.vus} (fixed, ${scenario.executor})`;
  }

  return `dynamic, preAllocatedVUs=${scenario.preAllocatedVUs}, maxVUs=${scenario.maxVUs} (${scenario.executor})`;
}

/**
 * Generates a random positive long integer.
 *
 * The value is between 1 and Number.MAX_SAFE_INTEGER (inclusive).
 *
 * @returns {number} Random positive integer
 */
export function generatePositiveLong(){
  return randomIntBetween(1, Number.MAX_SAFE_INTEGER)
}

/**
 * Generates a numeric string of fixed length.
 *
 * By default, the first digit is guaranteed to be non-zero.
 *
 * @param {number} len - Desired length
 * @returns {string} Generated numeric string
 */
export function generateNumericString(len) {
  let s = '';
  for (let i = 0; i < len; i++) {
    const d = i === 0 ? randomIntBetween(1, 9) : randomIntBetween(0, 9);
    s += String(d);
  }
  return s;
}

/**
 * Adds days to an epoch timestamp expressed in milliseconds.
 *
 * @param {number} epochMs - Epoch timestamp in milliseconds
 * @param {number} days - Days to add
 * @returns {number} New epoch timestamp in milliseconds
 */
export function addDays(epochMs, days) {
  return epochMs + (days * 24 * 60 * 60 * 1000);
}
