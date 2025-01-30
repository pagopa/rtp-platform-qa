import http from 'k6/http';
import { check } from 'k6';
import { sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { getValidAccessToken } from './utility.js';
import { generateRTPPayload } from './utility.js';

const config = {
    access_token_url: 'https://api-mcshared.uat.cstar.pagopa.it/auth/token',
    send_url: 'https://api-rtp.uat.cstar.pagopa.it/rtp/rtps'
};

const secrets = {
    debtor_service_provider: {
        client_id: __ENV.CLIENT_ID,
        client_secret: __ENV.CLIENT_SECRET,
        service_provider_id: __ENV.SERVICE_PROVIDER_ID,
    },
};

export const options = {
  discardResponseBodies: true,
  scenarios: {
    contacts: {
      executor: 'per-vu-iterations',
      vus: 10,
      iterations: 20,
      maxDuration: '5s',
    },
  },
};

let access_token;


export function setup() {
    access_token = getValidAccessToken(config.access_token_url, secrets.debtor_service_provider.client_id, secrets.debtor_service_provider.client_secret);
    return { access_token: access_token };
}

export default function (data) {
  const rtpPayload = generateRTPPayload();

  const sendHeaders = {
    'Version': 'v1',
    'RequestId': 'bd615b4a-066d-443e-8dd2-a28a39931fee',
    'Authorization': 'Bearer ' + data.access_token,
    'Content-Type': 'application/json'
  };

  const activateRes = http.post(config.send_url, JSON.stringify(rtpPayload), { headers: sendHeaders , discardResponseBodies: true });

    check(activateRes, {
        'status is 201': (r) => r.status === 201,
    });
}
