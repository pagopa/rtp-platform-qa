"""Helper functions to trigger debtor activation flows for specific service providers."""

from api.debtor_activation_api import activate
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_B_ID
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_ID
from api.debtor_activation_api import activate

def activate_with_sp_a(token: str, fiscal_code: str):
    """Activate a debtor using service provider A.

    Args:
        token: Bearer token used for authentication/authorization.
        fiscal_code: Debtor's fiscal code to be activated.

    Returns:
        The response returned by the underlying `activate` API.
    """
    return activate(
        token,
        fiscal_code,
        DEBTOR_SERVICE_PROVIDER_ID
    )


def activate_with_sp_b(token: str, fiscal_code: str):
    """Activate a debtor using service provider B.

    Args:
        token: Bearer token used for authentication/authorization.
        fiscal_code: Debtor's fiscal code to be activated.

    Returns:
        The response returned by the underlying `activate` API.
    """
    return activate(
        token,
        fiscal_code,
        DEBTOR_SERVICE_PROVIDER_B_ID,
    )
