"""Parse configuration file to obtain current settings.
"""
import os
from pathlib import Path
from dynaconf import Dynaconf

# Check if we're running in GitHub Actions
IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'

# Only load .env file if NOT in GitHub Actions
if not IS_GITHUB_ACTIONS:
    from dotenv import load_dotenv
    load_dotenv()
    print("Running locally - loaded .env file")
else:
    print("Running in GitHub Actions - using environment variables")

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

# Secrets configuration with automatic environment variable loading
secrets = Dynaconf(
    envvar_prefix='',  # No prefix for secrets
    environments=False,
    settings_files=['config/secrets.yaml'],
    # Enable automatic environment variable override
    auto_cast=True,
)
