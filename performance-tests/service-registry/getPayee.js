import http from 'k6/http';
import { check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { getValidAccessToken } from '../utility.js';
import { baseUrls, auth, serviceRegistry, secrets } from '../envVars.js';


const page = __ENV.PAGE || 0;
const size = __ENV.SIZE || 20;

const access_token_url = `${baseUrls.auth}${auth.getToken}`
const payeesUrl = `${baseUrls.sender}${serviceRegistry.getEnti}?page=${page}&size=${size}`
const client_id = secrets.clientId
const client_secret = secrets.clientSecret


export const options = {
    discardResponseBodies: true,
    scenarios: {
        contacts: {
            executor: 'constant-arrival-rate',
            duration: '5m',
            rate: 100,
            timeUnit: '1s',
            preAllocatedVUs: 100,
            maxVUs: 150,
        },
    },
};

let access_token;


export function setup() {
    access_token = getValidAccessToken(access_token_url, client_id, client_secret);
    return { access_token: access_token };
}

export default function (data) {
    const headers = {
        'Version': 'v1',
        'RequestId': uuidv4(),
        'Authorization': `Bearer ${data.access_token}`
    };

    const res = http.get(payeesUrl, { headers });

    check(res, {
        'status is 200': (r) => r.status === 200,
    });
}
