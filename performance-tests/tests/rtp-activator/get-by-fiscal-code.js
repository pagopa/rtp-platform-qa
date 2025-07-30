import http from 'k6/http';
import { check, sleep } from 'k6';
import {buildHeaders, endpoints, randomFiscalCode, setupAuth} from "../../utils/utils";

const {
    DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;

export function setup() {
    const { access_token } = setupAuth();
    const headers = buildHeaders(access_token);
    const fiscalCodes = [];

    console.log('Starting user activation...');
    for (let i = 0; i < 100; i++) {
        const fiscalCode = randomFiscalCode();
        const payload = {
            payer: {
                fiscalCode,
                rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
            }
        };

        const url = endpoints.activations;
        const res = http.post(url, JSON.stringify(payload), { headers });

        if (res.status === 201) {
            fiscalCodes.push(fiscalCode);
        } else {
            console.warn(`Activation Error: ${res.status}`);
        }

        sleep(0.1);
    }

    console.log(`Activations completed: ${fiscalCodes.length}`);
    console.log('Waiting 1 minute for it to cool down...');
    sleep(60);

    return { fiscalCodes, access_token };
}

export let options = {
    setupTimeout: '5m',
    scenarios: {
        get100: {
            executor: 'constant-arrival-rate',
            rate: 100,
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 200,
            maxVUs: 400,
            exec: 'getByFiscalCode',
            startTime: '70s'
        }
    },
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

export function getByFiscalCode(data) {
    const fiscalCode = data.fiscalCodes[Math.floor(Math.random() * data.fiscalCodes.length)];

    const headers = buildHeaders(data.access_token);
    headers['PayerId'] = fiscalCode;

    const url = endpoints.getByFiscalCode;
    const res = http.get(url, { headers });

    check(res, {'status is 200': r => r.status === 200});

    sleep(1);
    return res;
}