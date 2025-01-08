import schemathesis
from schemathesis import Case

from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.send_api_specification
BASE_URL = config.rtp_creation_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL + '/v1')


@schema.parametrize()
def test_send_rtp(case: Case):
    access_token = get_valid_access_token(client_id=secrets.creditor_service_provider.client_id,
                                          client_secret=secrets.creditor_service_provider.client_secret)
    case.call_and_validate(headers={'Authorization': access_token},
                           json={'payerId': secrets.creditor_service_provider.service_provider_id})
