import schemathesis
from schemathesis import Case

from config.configuration import config

SPEC_URL = config.activation_api_specification
BASE_URL = config.rtp_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL)


@schema.parametrize()
def test_activation(case: Case):
    case.call_and_validate()
