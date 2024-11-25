import schemathesis
from schemathesis import Case

from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.activation_api_specification
BASE_URL = config.activation_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL)


@schema.parametrize()
def test_activation(case: Case):
    access_token = get_valid_access_token(client_id=secrets.client_id,
                                          client_secret=secrets.client_secret)
    response = case.call_and_validate(headers={'Authorization': access_token})
