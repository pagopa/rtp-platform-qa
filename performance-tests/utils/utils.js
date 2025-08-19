import http from 'k6/http';
import { activationConfig } from '../config/config.js';

export const config = activationConfig;
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';


export const ActorCredentials = {
  DEBTOR_SERVICE_PROVIDER: 'DEBTOR_SERVICE_PROVIDER',
  CREDITOR_SERVICE_PROVIDER: 'CREDITOR_SERVICE_PROVIDER',
  SERVICE_REGISTRY_READER: 'SERVICE_REGISTRY_READER',
  PAGOPA_INTEGRATION_PAYEE_REGISTRY: 'PAGOPA_INTEGRATION_PAYEE_REGISTRY'
};


const ACTOR_CREDENTIALS_MAP = {
	[ActorCredentials.DEBTOR_SERVICE_PROVIDER]: {
		clientId: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
		clientSecret: __ENV.DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET,
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
 * @param {ActorCredentials} actor - The actor to fetch credentials for
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
 * Common options used across all test types.
 * These settings configure the metrics collection and tagging behavior.
 */
export const commonOptions = {
  summaryTrendStats: ['avg','min','med','max','p(90)','p(95)','p(99)'],
  systemTags: ['status','method','url','name','group','check','error','scenario'],
};

/**
 * Progressive test options with different test scenarios.
 * Contains predefined scenarios for different load testing strategies:
 * - stress_test: Gradually increases load to find system breaking points
 * - soak_test: Maintains constant moderate load for extended periods
 * - spike_test: Creates sudden burst of traffic to test recovery
 */
export const progressiveOptions = {
  ...commonOptions,
  scenarios: {
    stress_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 6000,
      exec: 'activate',
      stages: [
        { target: 30, duration: '1m' },
        { target: 50, duration: '30s' },
        { target: 100, duration: '30s' },
        { target: 100, duration: '30s' },
        { target: 250, duration: '30s' },
        { target: 250, duration: '30s' },
        { target: 500, duration: '30s' },
        { target: 500, duration: '30s' },
        { target: 1000, duration: '30s' },
        { target: 1000, duration: '30s' },
        { target: 2500, duration: '30s' },
        { target: 2500, duration: '30s' },
        { target: 5000, duration: '30s' },
        { target: 5000, duration: '60s' },
        { target: 1000, duration: '30s' },
        { target: 250, duration: '30s' },
        { target: 50, duration: '30s' }
      ]
    },
    soak_test: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 200,
      exec: 'activate'
    },
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 500,
      exec: 'activate',
      stages: [
        { target: 10, duration: '10s' },
        { target: 300, duration: '10s' },
        { target: 300, duration: '30s' },
        { target: 10, duration: '10s' }
      ]
    }
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
 * Determines the current test stage based on elapsed time.
 * Maps time windows to named stages that correspond with the stress test profile.
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
  getByFiscalCode: `${activationConfig.activation_base}/activations/payer`,
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
