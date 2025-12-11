import requests

from api.utils.endpoints import CBI_AUTH_URL
from api.utils.endpoints import MC_SHARED_AUTH_URL
from api.utils.endpoints import MC_SHARED_AUTH_URL_DEV


def get_valid_access_token(client_id: str, client_secret: str, access_token_function):
    token_response = access_token_function(client_id=client_id, client_secret=client_secret)
    token_response.raise_for_status()

    return f"Bearer {token_response.json()['access_token']}"


def get_access_token(client_id: str, client_secret: str):
    token_response = requests.post(
        MC_SHARED_AUTH_URL,
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }
    )

    return token_response

def get_access_token_dev(client_id: str, client_secret: str):
    token_response = requests.post(
        MC_SHARED_AUTH_URL_DEV,
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }
    )

    return token_response


def get_cbi_access_token(cert_path: str, key_path: str, authorization: str):
    token_response = requests.post(
        CBI_AUTH_URL,
        cert=(
            cert_path,
            key_path
        ),
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorization,
        },
        data={
            'grant_type': 'client_credentials',
            'scope': 'srtp'
        }
    )

    return token_response.json()['access_token']
