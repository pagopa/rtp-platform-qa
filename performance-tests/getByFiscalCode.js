import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';
import { getValidAccessToken } from './utility.js';

const {
    DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
    DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET,
    DEBTOR_SERVICE_PROVIDER_ID
} = __ENV;

const config = {
    access_token_url: 'https://api-mcshared.uat.cstar.pagopa.it/auth/token',
    base_url: 'https://api-rtp.uat.cstar.pagopa.it/rtp/activation',
};

export function setup() {
    const token = getValidAccessToken(
        config.access_token_url,
        DEBTOR_SERVICE_PROVIDER_CLIENT_ID,
        DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET
    );

    const fiscalCodes = [];

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Version': 'v1',
        'RequestId': uuidv4()
    };

    console.log('🚀 Avvio attivazione utenti...');
    for (let i = 0; i < 10; i++) {
        const fiscalCode = Math.floor(Math.random() * 1e11).toString().padStart(11, '0');
        const payload = {
            payer: {
                fiscalCode,
                rtpSpId: DEBTOR_SERVICE_PROVIDER_ID
            }
        };

        const res = http.post(
            `${config.base_url}/activations?toPublish=true`,
            JSON.stringify(payload),
            { headers }
        );

        if (res.status === 201) {
            fiscalCodes.push(fiscalCode);
        } else {
            console.warn(`❌ Errore attivazione: ${res.status}`);
        }

        sleep(0.1);
    }

    console.log(`✅ Attivazioni completate: ${fiscalCodes.length}`);
    console.log('⏳ In attesa di 1 minuto per freddamento...');
    sleep(60);

    return { fiscalCodes, token };
}

export let options = {
    setupTimeout: '180s',

    scenarios: {
        /*
        get10: {
            executor: 'constant-arrival-rate',
            rate: 10,
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 50,
            exec: 'getByFiscalCode',
            startTime: '0s'
        },
        */
        /*
        get100: {
            executor: 'constant-arrival-rate',
            rate: 100,
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 200,
            exec: 'getByFiscalCode',
            startTime: '40s'
        },
        */
        /*
        get500: {
            executor: 'constant-arrival-rate',
            rate: 500,
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 400,
            exec: 'getByFiscalCode',
            startTime: '80s'
        },*/
        /*
        get1000: {
            executor: 'constant-arrival-rate',
            rate: 1000,
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 600,
            exec: 'getByFiscalCode',
            startTime: '120s'
        }
         */
    },
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

export function getByFiscalCode(data) {
    const fiscalCode = data.fiscalCodes[Math.floor(Math.random() * data.fiscalCodes.length)];

    const headers = {
        'Authorization': `Bearer ${data.token}`,
        'Version': 'v1',
        'RequestId': uuidv4(),
        'PayerId': fiscalCode
    };

    const res = http.get(`${config.base_url}/activations/payer`, { headers });

    check(res, {
        'status is 200': r => r.status === 200,
        'has body': r => r.body && r.body.length > 0
    });

    sleep(0.1);
}