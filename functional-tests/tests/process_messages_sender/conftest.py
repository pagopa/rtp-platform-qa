import pytest

from api.auth_api import get_access_token, get_valid_access_token
from config.configuration import secrets

# ============================================================
# Access token to access process GPD sender API
# ============================================================


@pytest.fixture
def rtp_consumer_access_token() -> str:
    """
    Access token for RTP Consumer client.
    Used to send messages directly to the GPD sender service.
    """
    return get_valid_access_token(
        client_id=secrets.rtp_consumer.client_id,
        client_secret=secrets.rtp_consumer.client_secret,
        access_token_function=get_access_token,
    )
