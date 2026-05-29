"""Contract tests for the RTP Activation API.

Validates that the API conforms to its OpenAPI specification by checking:
- response status codes are among those documented in the spec
- response bodies match the documented schemas
- no server errors (5xx) are returned
"""

import uuid

import allure
import schemathesis
from contract_checks import CONTRACT_CHECKS
from schemathesis import Case

from api.auth_api import get_keycloak_access_token, get_valid_access_token
from config.configuration import config, secrets

SPEC_URL = config.activation_api_specification
BASE_URL = config.activation_base_url_path

schema = schemathesis.openapi.from_url(SPEC_URL)

ACCESS_TOKEN = get_valid_access_token(
    client_id=secrets.debtor_service_provider.client_id,
    client_secret=secrets.debtor_service_provider.client_secret,
    access_token_function=get_keycloak_access_token,
)


@allure.label("parentSuite", "contract-tests.tests")
@allure.feature("RTP Activation")
@schema.parametrize()
def test_activation_contract(case: Case):
    """Parametrized contract test generated from the Activation API OpenAPI spec.

    Schemathesis derives one test case per endpoint defined in the spec, generating
    request data (path params, query params, body) that is valid according to the schema.
    Each case is executed against the live API and the response is validated with
    CONTRACT_CHECKS.
    """
    case.headers = {
        "Authorization": ACCESS_TOKEN,
        "RequestId": str(uuid.uuid4()),
        "Version": "v1",
        **{k: v for k, v in (case.headers or {}).items() if k.lower() not in {"authorization", "requestid", "version"}},
    }

    response = case.call(base_url=BASE_URL)
    case.validate_response(response, checks=CONTRACT_CHECKS)
