from api.auth import get_valid_access_token
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset import generate_rtp_data


def test_send_rtp_api():
    rtp_data = generate_rtp_data()
    access_token = get_valid_access_token(client_id=secrets.client_id, client_secret=secrets.client_secret)

    response = send_rtp(access_token=access_token, rtp_payload=rtp_data)
    assert response.status_code == 201
