import allure
import pytest

from api.landing_page import landing_page

@allure.feature('Web page')
@allure.story('The RTP web page is reachable')
@allure.title('The RTP web page is reachable')
@pytest.mark.landing_page
@pytest.mark.happy_path
def test_send_rtp():
    response = landing_page()
    assert response.status_code == 200
