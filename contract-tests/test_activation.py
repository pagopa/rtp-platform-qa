import uuid

import allure
import schemathesis
from schemathesis import Case

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.activation_api_specification

BASE_URL = "https://api-rtp.uat.cstar.pagopa.it/rtp/activation"

schema = schemathesis.openapi.from_url(SPEC_URL)


@allure.label("parentSuite", "contract-tests.tests")
@allure.feature("RTP Activation")
@schema.parametrize()
def test_activation(case: Case):
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )

    request_id = str(uuid.uuid4())

    case.call_and_validate(
        base_url=BASE_URL,
        headers={
            "Authorization": access_token,
            "RequestId": request_id,
            "Version": "v1",
        },
    )
