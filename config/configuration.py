"""Parse configuration file to obtain current settings.
"""
from dynaconf import Dynaconf

IDPAY_ENV_VAR_PREFIX = 'RTP'

# `envvar_prefix` = export envvars with RTP_ENV_VAR_PREFIX as prefix.
# `settings_files` = Load settings files in the order.
config = Dynaconf(
    envvar_prefix=IDPAY_ENV_VAR_PREFIX,
    settings_files=['config.yaml'],
)
