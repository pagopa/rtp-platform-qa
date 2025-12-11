import uuid

import allure
import requests
import schemathesis
from schemathesis import Case

from api.auth_api import get_access_token
from api.auth_api import get_valid_access_token
from config.configuration import config
from config.configuration import secrets

SPEC_URL = config.send_api_specification
BASE_URL = config.rtp_creation_base_url_path

schema = schemathesis.openapi.from_url(SPEC_URL)

ACCESS_TOKEN = get_valid_access_token(
    client_id=secrets.creditor_service_provider.client_id,
    client_secret=secrets.creditor_service_provider.client_secret,
    access_token_function=get_access_token,
)


@allure.label('parentSuite', 'contract-tests.tests')
@allure.feature('RTP Send')
@schema.parametrize()
def test_send_rtp(case: Case):
    request_id = str(uuid.uuid4())

    request_kwargs: dict = {
        'method': case.method,
        'url': BASE_URL.rstrip('/') + case.path,
        'headers': {
            'Authorization': ACCESS_TOKEN,
            'RequestId': request_id,
            'Version': 'v1',
            **{
                h: v
                for h, v in (case.headers or {}).items()
                if h.lower() not in {'authorization', 'requestid', 'version'}
            },
        },
        'params': case.query,
    }

    if isinstance(case.body, (dict, list)):
        request_kwargs['json'] = case.body

    response = requests.request(**request_kwargs)

    assert 100 <= response.status_code < 600

    if response.headers.get('Content-Type', '').startswith('application/json'):
        _ = response.json()
