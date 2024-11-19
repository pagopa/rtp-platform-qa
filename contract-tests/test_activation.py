import schemathesis
from schemathesis import Case

from api.auth import get_valid_token
from config.configuration import config

SPEC_URL = config.activation_api_specification
BASE_URL = config.rtp_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL)


@schema.parametrize()
def test_activation(case: Case):
    if 'simulate_403' in case.path:
        case.headers['Authorization'] = 'Bearer InvalidToken'
    else:
        valid_token = get_valid_token()
        case.headers['Authorization'] = get_valid_token()

    response = case.call_and_validate()

    if case.headers['Authorization'] == 'Bearer InvalidToken':
        assert response.status_code == 403
    else:
        response.raise_for_status()
