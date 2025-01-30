import http from 'k6/http';

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


export function generateRTPPayload(payerId) {
    const noticeNumber = Array.from({ length: 18 }, () => Math.floor(Math.random() * 10)).join('');
    const amount = (Math.random() * 999999);
    const description = 'Paga questo avviso';
    const expiryDate = new Date(Date.now() + Math.floor(Math.random() * 365) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    if (!payerId) {
        payerId = 'AAABBB01A01A001A';
    }

    const payee = {
         "name": "Comune di Smartino",
        "payeeId": "77777777777",
        "payTrxRef": "ABC/124"
    };

    const payer = {
        name: 'Pigrolo',
        payerId: payerId
    };

    const paymentNotice = {
        noticeNumber: noticeNumber,
        amount: parseFloat(amount),
        description: description,
        subject: 'TARI 2025',
        expiryDate: expiryDate,
    };

    return {
        payee: payee,
        payer: payer,
        paymentNotice: paymentNotice
    };
}
