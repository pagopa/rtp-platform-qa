"""Utility to generate DS-08N negative (RJCT) callback payloads for v2 callback tests.

The generated payload mimics the v2 callback sent for an asynchronous SEPA
Request-to-Pay response with a rejected (`RJCT`) transaction status. Applied
on a `SENT` RTP it rejects it (`REJECTED`); applied on an `ACCEPTED` RTP
(after a prior DS-05 ACTC callback) it transitions it to `USER_REJECTED`.
"""

import uuid

from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.datetime_utils import generate_create_time, generate_future_time
from utils.generators_utils import generate_random_string
from utils.type_utils import JsonType

RJCT_STATUS = "RJCT"
INVALID_STATUS = "INVALID"


def generate_callback_data_DS_08N_negative_compliant(bic: str = DEBTOR_SERVICE_PROVIDER_C_ID) -> JsonType:
    """Generate a DS-08N RJCT compliant callback payload (v2).

    Args:
        bic: Bank Identifier Code of the initiating party
            (defaults to the Debtor Service Provider C id, MOCKSP05).

    Returns:
        JsonType: JSON-serializable DS-08N callback payload,
        ready to be used in v2 callback tests.
    """
    return _generate_callback_data_DS_08N(bic=bic, status=RJCT_STATUS)


def generate_non_compliant_callback_data_DS_08N_negative(bic: str = DEBTOR_SERVICE_PROVIDER_C_ID) -> JsonType:
    """Generate a DS-08N non-compliant callback payload (v2).

    The payload simulates a v2 callback with an invalid transaction status,
    used to test the system's handling of non-compliant callbacks.

    Args:
        bic: Bank Identifier Code of the initiating party
            (defaults to the Debtor Service Provider C id, MOCKSP05).

    Returns:
        JsonType: JSON-serializable DS-08N callback payload with invalid
        status, ready to be used in v2 callback tests.
    """
    return _generate_callback_data_DS_08N(bic=bic, status=INVALID_STATUS)


def _generate_callback_data_DS_08N(bic: str, status: str) -> JsonType:
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"
    message_id = str(uuid.uuid4())

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    return {
        "resourceId": resource_id,
        "AsynchronousSepaRequestToPayResponse": {
            "Document": {
                "CdtrPmtActvtnReqStsRpt": {
                    "GrpHdr": {
                        "MsgId": message_id,
                        "CreDtTm": create_time,
                        "InitgPty": {"Id": {"OrgId": {"AnyBIC": bic}}},
                    },
                    "OrgnlGrpInfAndSts": {
                        "OrgnlMsgId": original_msg_id,
                        "OrgnlMsgNmId": "pain.013.001.07",
                        "OrgnlCreDtTm": original_time,
                    },
                    "OrgnlPmtInfAndSts": [
                        {
                            "OrgnlPmtInfId": str(uuid.uuid4()),
                            "TxInfAndSts": {"TxSts": status},
                        }
                    ],
                }
            }
        },
        "_links": {
            "initialSepaRequestToPayUri": {
                "href": f"https://example.org/sepa-request-to-pay-requests/{resource_id}",
            }
        },
    }