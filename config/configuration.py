"""Parse configuration file to obtain current settings.
"""
import os
from pathlib import Path

from dynaconf import Dynaconf

BASE_DIR = Path(__file__).parent.parent.resolve()

RTP_ENV_VAR_PREFIX = 'RTP'

# `envvar_prefix` = export envvars with RTP_ENV_VAR_PREFIX as prefix.
# `settings_files` = Load settings files in the order.
config = Dynaconf(
    envvar_prefix=RTP_ENV_VAR_PREFIX,
    settings_files=['config.yaml'],
)
config.cert_path = str(BASE_DIR / config.cert_path)
config.key_path  = str(BASE_DIR / config.key_path)

secrets = Dynaconf(
    envvar_prefix='',  # No prefix for secrets
    environments=False,  # Disable environment switching
    settings_files=[],  # No files, only environment variables
)

secrets.debtor_service_provider = Dynaconf(
    client_id=os.getenv('DEBTOR_SERVICE_PROVIDER_CLIENT_ID'),
    service_provider_id=os.getenv('DEBTOR_SERVICE_PROVIDER_ID'),
    client_secret=os.getenv('DEBTOR_SERVICE_PROVIDER_CLIENT_SECRET'),
)

secrets.debtor_service_provider_B = Dynaconf(
    client_id=os.getenv('DEBTOR_SERVICE_PROVIDER_B_CLIENT_ID'),
    service_provider_id=os.getenv('DEBTOR_SERVICE_PROVIDER_B_ID'),
    client_secret=os.getenv('DEBTOR_SERVICE_PROVIDER_B_CLIENT_SECRET'),
)

secrets.creditor_service_provider = Dynaconf(
    client_id=os.getenv('CREDITOR_SERVICE_PROVIDER_CLIENT_ID'),
    service_provider_id=os.getenv('CREDITOR_SERVICE_PROVIDER_ID'),
    client_secret=os.getenv('CREDITOR_SERVICE_PROVIDER_CLIENT_SECRET'),
)

secrets.pagopa_integration_payee_registry = Dynaconf(
    client_id=os.getenv('PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_ID'),
    client_secret=os.getenv('PAGOPA_INTEGRATION_PAYEE_REGISTRY_CLIENT_SECRET'),
)

secrets.pagopa_integration_service_registry = Dynaconf(
    client_id=os.getenv('PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_ID'),
    client_secret=os.getenv('PAGOPA_INTEGRATION_SERVICE_REGISTRY_CLIENT_SECRET'),
)

secrets.webpage = Dynaconf(
    username=os.getenv('WEBPAGE_USERNAME'),
    password=os.getenv('WEBPAGE_PASSWORD'),
)

# Direct attributes for backward compatibility
secrets.CBI_client_id = os.getenv('CBI_CLIENT_ID')
secrets.CBI_client_secret = os.getenv('CBI_CLIENT_SECRET')
secrets.CBI_client_PFX_base64 = os.getenv('CBI_CLIENT_PFX_BASE64')
secrets.CBI_client_PFX_password_base64 = os.getenv('CBI_CLIENT_PFX_PASSWORD_BASE64')
secrets.debtor_service_provider_mock_PFX_base64 = os.getenv('DEBTOR_SERVICE_PROVIDER_MOCK_PFX_BASE64')
secrets.debtor_service_provider_mock_PFX_password_base64 = os.getenv('DEBTOR_SERVICE_PROVIDER_MOCK_PFX_PASSWORD_BASE64')
secrets.cbi_activated_fiscal_code = os.getenv('CBI_ACTIVATED_FISCAL_CODE')
secrets.poste_activated_fiscal_code = os.getenv('POSTE_ACTIVATED_FISCAL_CODE')
