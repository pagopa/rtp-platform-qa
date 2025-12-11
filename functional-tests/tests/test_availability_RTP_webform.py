import allure
import pytest

from api.RTP_landing_page_api import landing_page

@allure.epic('RTP Webform Availability')
@allure.feature('Web page')
@allure.story('The RTP web page is reachable')
@allure.title('The RTP web page is reachable')
@allure.tag('functional', 'happy_path', 'landing_page', 'rtp_webform_availability')
@pytest.mark.webform
@pytest.mark.landing_page
@pytest.mark.happy_path
def test_send_rtp():
    response = landing_page()
    assert response.status_code == 200
