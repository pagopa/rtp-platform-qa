import requests

from api.utils.endpoints import DEBT_POSITIONS_DELETE_URL
from api.utils.endpoints import DEBT_POSITIONS_DELETE_URL_DEV
from api.utils.endpoints import DEBT_POSITIONS_UPDATE_URL
from api.utils.endpoints import DEBT_POSITIONS_UPDATE_URL_DEV
from api.utils.endpoints import DEBT_POSITIONS_URL
from api.utils.endpoints import DEBT_POSITIONS_URL_DEV
from api.utils.http_utils import APPLICATION_JSON_HEADER
from api.utils.http_utils import HTTP_TIMEOUT

def create_debt_position(
    subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True, is_dev: bool = False
) -> requests.Response:
    """API to create a debt position and optionally publish it.

    Args:
        subscription_key (str): API subscription key
        organization_id (str): Organization ID
        payload (dict): The debt position data
        to_publish (bool): Whether to publish the debt position
        is_dev (bool): Whether to use the development environment

    Returns:
        Response: HTTP response from the API call
    """
    if is_dev:
        url = DEBT_POSITIONS_URL_DEV
    else:
        url = DEBT_POSITIONS_URL

    return requests.post(
        url=url.format(organizationId=organization_id),
        headers={
            'ocp-apim-subscription-key': subscription_key,
            **APPLICATION_JSON_HEADER,
        },
        params={'toPublish': to_publish},
        json=payload,
        timeout=HTTP_TIMEOUT,
    )

def delete_debt_position(
    subscription_key: str, organization_id: str, iupd: str, is_dev: bool = False
) -> requests.Response:
    """API to delete a debt position.

    Args:
        subscription_key (str): API subscription key
        organization_id (str): Organization ID
        iupd (str): Unique Debt Position Identifier
        is_dev (bool): Whether to use the development environment

    Returns:
        Response: HTTP response from the API call
    """
    if is_dev:
        url = DEBT_POSITIONS_DELETE_URL_DEV
    else:
        url = DEBT_POSITIONS_DELETE_URL
    url = url.format(organizationId=organization_id, iupd=iupd)

    headers = {
        'ocp-apim-subscription-key': subscription_key,
        **APPLICATION_JSON_HEADER
    }

    return requests.delete(url, headers=headers, timeout=HTTP_TIMEOUT)

def update_debt_position(
    subscription_key: str,
    organization_id: str,
    iupd: str,
    payload: dict,
    to_publish: bool = True,
    is_dev: bool = False
) -> requests.Response:
    """
    API to update an existing debt position.

    Args:
        subscription_key (str): API subscription key
        organization_id (str): Organization ID
        iupd (str): Unique Debt Position Identifier
        payload (dict): The updated debt position data
        to_publish (bool): Whether to publish the updated debt position
        is_dev (bool): Whether to use the development environment

    Returns:
        Response: HTTP response from the API call
    """
    if is_dev:
        url = DEBT_POSITIONS_UPDATE_URL_DEV.format(organizationId=organization_id, iupd=iupd)
    else:
        url = DEBT_POSITIONS_UPDATE_URL.format(organizationId=organization_id, iupd=iupd)
    headers = {
        'ocp-apim-subscription-key': subscription_key,
        **APPLICATION_JSON_HEADER
    }

    return requests.put(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT, params={'toPublish': to_publish})
def get_debt_position(
    subscription_key: str, organization_id: str, iupd: str, is_dev: bool = False
) -> requests.Response:
    """API to get a debt position by IUPD.

    Args:
        subscription_key (str): API subscription key
        organization_id (str): Organization ID
        iupd (str): Unique Debt Position Identifier
        is_dev (bool): Whether to use the development environment

    Returns:
        Response: HTTP response from the API call
    """
    if is_dev:
        base_url = DEBT_POSITIONS_URL_DEV
    else:
        base_url = DEBT_POSITIONS_URL

    url = base_url.format(organizationId=organization_id) + f"/{iupd}"

    return requests.get(
        url=url,
        headers={
            'ocp-apim-subscription-key': subscription_key,
            **APPLICATION_JSON_HEADER,
        },
        timeout=HTTP_TIMEOUT,
    )

def create_debt_position_dev(subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True) -> requests.Response:
    return create_debt_position(subscription_key, organization_id, payload, to_publish, is_dev=True)

def delete_debt_position_dev(subscription_key: str, organization_id: str, iupd: str) -> requests.Response:
    return delete_debt_position(subscription_key, organization_id, iupd, is_dev=True)

def update_debt_position_dev(subscription_key: str, organization_id: str, iupd: str, payload: dict, to_publish: bool = True) -> requests.Response:
    return update_debt_position(subscription_key, organization_id, iupd, payload, to_publish, is_dev=True)

def get_debt_position_dev(subscription_key: str, organization_id: str, iupd: str) -> requests.Response:
    return get_debt_position(subscription_key, organization_id, iupd, is_dev=True)
