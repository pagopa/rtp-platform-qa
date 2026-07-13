"""Named error codes returned by the Debtor Activation API in ``errors[].code`` / ``errors[].description``.

Import ``ActivationErrorCode`` wherever a test needs to assert on one of these
error responses instead of hardcoding the raw code/description strings.
"""

from enum import Enum


class ActivationErrorCode(Enum):
    INVALID_FISCAL_CODE_FORMAT = ("01021002E", "Invalid fiscal code format.")
    INVALID_SERVICE_PROVIDER_ID_FORMAT = ("01021003E", "Invalid RTP Service Provider ID format.")
    USER_ALREADY_ACTIVE = ("01031006E", "User is already active")

    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description