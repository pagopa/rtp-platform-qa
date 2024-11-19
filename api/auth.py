import requests

from config.configuration import config
from config.configuration import secrets


def get_valid_token():
    token_response = requests.post(
        config.mcshared_auth_url,
        data={
            'grant_type': 'client_credentials',
            'client_id': secrets.client_id,
            'client_secret': secrets.client_secret,
        }
    )
    token_response.raise_for_status()
    return f"Bearer {token_response.json()['access_token']}"
