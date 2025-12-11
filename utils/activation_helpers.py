"""Helper functions to trigger debtor activation flows for specific service providers."""

from api.activation import activate
from config.configuration import secrets

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
        secrets.debtor_service_provider.service_provider_id,
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
        secrets.debtor_service_provider_B.service_provider_id,
    )
