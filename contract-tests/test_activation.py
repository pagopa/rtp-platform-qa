import allure
import pytest
import schemathesis
from schemathesis import Case

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.activation_api_specification
BASE_URL = config.rtp_creation_base_url_path

schema = schemathesis.openapi.from_uri(SPEC_URL, base_url=BASE_URL)


@allure.feature("RTP Activation")
@schema.parametrize()
def test_activation(case: Case):
    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token,
    )
    case.call_and_validate(
        headers={"Authorization": access_token},
    )
