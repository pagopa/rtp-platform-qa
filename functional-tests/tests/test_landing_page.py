import pytest

from api.landing_page import landing_page


@pytest.mark.landing_page
def test_send_rtp():
    response = landing_page()
    assert response.status_code == 200
