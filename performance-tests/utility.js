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
