import requests

from config.configuration import config

DEBT_POSITIONS_URL = config.debt_positions_base_url_path + config.debt_positions_path

def create_debt_position(subscription_key: str,
                         organization_id: str,
                         payload: dict,
                         to_publish: bool = True) -> requests.Response:
    """API to create a debt position and optionally publish it."""
    return requests.post(
        url=DEBT_POSITIONS_URL.format(organizationId=organization_id),
        headers={
            'ocp-apim-subscription-key': subscription_key,
            'Content-Type': 'application/json'
        },
        params={'toPublish': to_publish},
        json=payload,
        timeout=config.default_timeout
    )