# auth.py
import requests
from utilities import require_env

from config import AUTH_URL


CLIENT_ID = require_env('DEBTOR_SERVICE_PROVIDER_CLIENT_ID')
CLIENT_SECRET = require_env('DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET')


def get_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError('Missing CLIENT_ID or CLIENT_SECRET in environment variables')

    resp = requests.post(
        AUTH_URL,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        },
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()['access_token']

if __name__ == '__main__':
    print(get_token())
