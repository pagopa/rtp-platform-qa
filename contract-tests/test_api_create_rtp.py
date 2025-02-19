import allure
import schemathesis
from schemathesis import Case

from config.configuration import config

SPEC_URL = config.create_rtp_api_specification
BASE_URL = config.rtp_creation_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL)

@allure.feature('RTP Send')
@schema.parametrize()
def test_create_rtp(case: Case):
    case.call_and_validate()
