import pytest
import requests
import schemathesis
from schemathesis import Case

from config.configuration import config

SPEC_URL = 'https://raw.githubusercontent.com/pagopa/rtp-apis/refs/heads/main/src/rtp/api/pagopa/openapi.yaml'
BASE_URL = config.rtp_base_url_path

schema = schemathesis.from_uri(SPEC_URL, base_url=BASE_URL)


@schema.parametrize()
def test_create_rtp(case: Case):
    case.call_and_validate()
