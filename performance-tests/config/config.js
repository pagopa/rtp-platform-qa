/**
 * Environment-aware configuration for k6 performance tests.
 *
 * The target environment can be selected at run time via the `ENVIRONMENT`
 * k6 variable (e.g. `k6 run -e ENVIRONMENT=dev ...`). Defaults to `uat` to
 * preserve the previous hardcoded behavior when the variable is not set.
 */
const ENVIRONMENT = (typeof __ENV !== 'undefined' && __ENV.ENVIRONMENT) || 'uat';

const HOST_SUFFIXES = {
  dev: 'dev.cstar.pagopa.it',
  uat: 'uat.cstar.pagopa.it'
};

if (!Object.prototype.hasOwnProperty.call(HOST_SUFFIXES, ENVIRONMENT)) {
  throw new Error(`❌ Unsupported ENVIRONMENT '${ENVIRONMENT}'. Supported values: ${Object.keys(HOST_SUFFIXES).join(', ')}`);
}

/** Host suffix for the selected environment (e.g. `dev.cstar.pagopa.it`). Exported for
 * modules that need to build environment-aware values outside of this file's configs
 * (e.g. mTLS `tlsAuth.domains` in the rtp-sender callback test scripts). */
export const HOST_SUFFIX = HOST_SUFFIXES[ENVIRONMENT];
const ACCESS_TOKEN_URL = `https://api-mcshared.${HOST_SUFFIX}/auth-itn/realms/srtp/protocol/openid-connect/token`;

export const activationConfig = {
  access_token_url: ACCESS_TOKEN_URL,
  activation_base: `https://api-rtp.${HOST_SUFFIX}/rtp/activation`
};

export const senderConfig = {
  access_token_url: ACCESS_TOKEN_URL,
  sender_base: `https://api-rtp.${HOST_SUFFIX}/rtp`
};

export const serviceRegistryConfig = {
  accessTokenUrl: ACCESS_TOKEN_URL,
  baseUrl: `https://api-rtp.${HOST_SUFFIX}/rtp/service_providers`
};

export const callbackConfig = {
  callback_base: `https://api-rtp-cb.${HOST_SUFFIX}/rtp`
};
