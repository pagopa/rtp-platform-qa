import uuid

import requests

from config.configuration import config


DEBT_POSITIONS_URL = config.debt_positions_base_url_path + config.debt_positions_path
DEBT_POSITIONS_DEV_URL = (
    config.debt_positions_dev_base_url_path + config.debt_positions_dev_path
)


DEBT_POSITIONS_DELETE_URL = config.debt_positions_base_url_path + config.debt_positions_delete_path
DEBT_POSITIONS_DELETE_DEV_URL = config.debt_positions_dev_base_url_path + config.debt_positions_dev_delete_path



def create_debt_position(
    subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True
) -> requests.Response:
    """API to create a debt position and optionally publish it."""
    return requests.post(
        url=DEBT_POSITIONS_URL.format(organizationId=organization_id),
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        params={'toPublish': to_publish},
        json=payload,
        timeout=config.default_timeout,
    )


def create_debt_position_dev(
    subscription_key: str, organization_id: str, payload: dict, to_publish: bool = True
) -> requests.Response:
    """API to create a debt position in DEV environment and optionally publish it."""
    return requests.post(
        url=DEBT_POSITIONS_DEV_URL.format(organizationId=organization_id),
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        params={'toPublish': to_publish},
        json=payload,
        timeout=config.default_timeout,
    )

def delete_debt_position(subscription_key, organization_id, iupd):
    """
    API to delete a debt position.
    """
    url = DEBT_POSITIONS_DELETE_URL.format(organizationId=organization_id, iupd=iupd)

    headers = {
        'ocp-apim-subscription-key': subscription_key,
        'Content-Type': 'application/json'
    }

    response = requests.delete(url, headers=headers, timeout=config.default_timeout)
    return response

def delete_debt_position_dev(subscription_key, organization_id, iupd):
    """
    API to delete a debt position in DEV environment.
    """
    url = DEBT_POSITIONS_DELETE_DEV_URL.format(organizationId=organization_id, iupd=iupd)

    headers = {
        'ocp-apim-subscription-key': subscription_key,
        'Content-Type': 'application/json'
    }

    response = requests.delete(url, headers=headers, timeout=config.default_timeout)
    return response


def get_debt_position(
    subscription_key: str, organization_id: str, iupd: str
) -> requests.Response:
    """API to get a debt position by IUPD."""
    url = DEBT_POSITIONS_URL.format(organizationId=organization_id) + f"/{iupd}"
    return requests.get(
        url=url,
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        timeout=config.default_timeout,
    )

def get_debt_position_dev(
    subscription_key: str, organization_id: str, iupd: str
) -> requests.Response:
    """API to get a debt position by IUPD in DEV environment."""
    url = DEBT_POSITIONS_DEV_URL.format(organizationId=organization_id) + f"/{iupd}"
    return requests.get(
        url=url,
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json',
        },
        timeout=config.default_timeout,
    )
