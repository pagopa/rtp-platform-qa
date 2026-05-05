import uuid

import requests

from api.utils.api_version import PAYEES_VERSION
from api.utils.endpoints import PAYEES_CONSENTS_URL, PAYEES_URL
from api.utils.http_utils import HTTP_TIMEOUT
from utils.datetime_utils import get_date_or_today

CONSENTS_DEFAULT_PAGE_SIZE = 20
CONSENTS_DEFAULT_PAGE_NUMBER = 0
CONSENTS_DEFAULT_VALUE = "OPT_OUT"


def get_payee_registry(access_token: str, page: int = 0, size: int = 20):

    return requests.get(
        url=PAYEES_URL,
        headers={"Authorization": access_token, "Version": PAYEES_VERSION, "RequestId": str(uuid.uuid4())},
        params={"page": page, "size": size},
        timeout=HTTP_TIMEOUT,
    )


def get_payees_consents(
    access_token: str,
    page_number: int = CONSENTS_DEFAULT_PAGE_NUMBER,
    page_size: int = CONSENTS_DEFAULT_PAGE_SIZE,
    consent: str | None = CONSENTS_DEFAULT_VALUE,
    from_date: str | None = None,
    to_date: str | None = None,
) -> requests.Response:
    params: dict = {"pageNumber": page_number, "pageSize": page_size}
    if consent is not None:
        params["consent"] = consent
    if from_date is not None:
        params["fromDate"] = from_date
    params["toDate"] = get_date_or_today(to_date)

    return requests.get(
        url=PAYEES_CONSENTS_URL,
        headers={"Authorization": access_token, "Version": PAYEES_VERSION, "RequestId": str(uuid.uuid4())},
        params=params,
        timeout=HTTP_TIMEOUT,
    )
