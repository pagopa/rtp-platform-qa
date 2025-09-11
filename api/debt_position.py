import requests

from config.configuration import config

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
        url = config.debt_positions_dev_base_url_path + config.debt_positions_dev_path
    else:
        url = config.debt_positions_base_url_path + config.debt_positions_path

    return requests.post(
        url=url.format(organizationId=organization_id),
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        params={'toPublish': to_publish},
        json=payload,
        timeout=config.default_timeout,
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
        url = config.debt_positions_dev_base_url_path + config.debt_positions_dev_delete_path
    else:
        url = config.debt_positions_base_url_path + config.debt_positions_delete_path

    url = url.format(organizationId=organization_id, iupd=iupd)

    headers = {
        'ocp-apim-subscription-key': subscription_key,
        'Content-Type': 'application/json'
    }

    return requests.delete(url, headers=headers, timeout=config.default_timeout)

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
        url = (config.debt_positions_dev_base_url_path +
               config.debt_positions_dev_update_path.format(organizationId=organization_id, iupd=iupd))
    else:
        url = (config.debt_positions_base_url_path +
               config.debt_positions_update_path.format(organizationId=organization_id, iupd=iupd))

    headers = {
        'ocp-apim-subscription-key': subscription_key,
        'Content-Type': 'application/json'
    }

    return requests.put(url, headers=headers, json=payload, timeout=config.default_timeout, params={'toPublish': to_publish})

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
        base_url = config.debt_positions_dev_base_url_path + config.debt_positions_dev_path
    else:
        base_url = config.debt_positions_base_url_path + config.debt_positions_path

    url = base_url.format(organizationId=organization_id) + f"/{iupd}"

    return requests.get(
        url=url,
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        timeout=config.default_timeout,
    )

def create_debt_position_dev(subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True) -> requests.Response:
    return create_debt_position(subscription_key, organization_id, payload, to_publish, is_dev=True)

def delete_debt_position_dev(subscription_key: str, organization_id: str, iupd: str) -> requests.Response:
    return delete_debt_position(subscription_key, organization_id, iupd, is_dev=True)

def update_debt_position_dev(subscription_key: str, organization_id: str, iupd: str, payload: dict, to_publish: bool = True) -> requests.Response:
    return update_debt_position(subscription_key, organization_id, iupd, payload, to_publish, is_dev=True)

def get_debt_position_dev(subscription_key: str, organization_id: str, iupd: str) -> requests.Response:
    return get_debt_position(subscription_key, organization_id, iupd, is_dev=True)
