import allure
import pytest
import schemathesis
from schemathesis import Case

from api.auth import get_access_token
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.create_rtp_api_specification
BASE_URL = config.rtp_creation_base_url_path

schema = schemathesis.loaders.from_uri(SPEC_URL, base_url=BASE_URL + "/v1")


@allure.feature('RTP Send')
@schema.parametrize()
def test_create_rtp(case: Case):
    access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret,
        access_token_function=get_access_token,
    )
    case.call_and_validate(
        headers={"Authorization": access_token},
        json={"payerId": secrets.creditor_service_provider.service_provider_id},
    )


pytest.skip(
    "Skipping create RTP contract tests: CREATE_RTP_API_SPECIFICATION missing in config",
    allow_module_level=True,
)
