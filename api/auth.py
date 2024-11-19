import requests

from config.configuration import config


def get_valid_token(client_id: str, client_secret: str):
    token_response = requests.post(
        config.mcshared_auth_url,
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }
    )
    token_response.raise_for_status()
    return f"Bearer {token_response.json()['access_token']}"
