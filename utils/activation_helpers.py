from api.activation import activate
from config.configuration import secrets

def activate_with_sp_a(token: str, fiscal_code: str):
    return activate(
        token,
        fiscal_code,
        secrets.debtor_service_provider.service_provider_id,
    )


def activate_with_sp_b(token: str, fiscal_code: str):
    return activate(
        token,
        fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
    )
