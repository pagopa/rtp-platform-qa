"""Parse configuration file to obtain current settings.
"""
import logging
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

# Load the secrets for the specified environment
secrets = {}

try:
    all_secrets = Dynaconf(settings_files=config.SECRET_PATH)
    if config.TARGET_ENV in all_secrets:
        secrets = all_secrets[config.TARGET_ENV]
except AttributeError as e:
    logging.error(e)
    exit()
