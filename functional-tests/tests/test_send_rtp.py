from api.send_rtp import send_rtp
from utils.dataset import generate_rtp_data


def test_send_rtp_api():
    rtp_data = generate_rtp_data()

    response = send_rtp(rtp_data)
    assert response.status_code == 200
