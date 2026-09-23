"""Generate EPC 4.0 RTP status-update callback payloads."""

import uuid

from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.datetime_utils import generate_create_time
from utils.type_utils import JsonType


def generate_status_update_callback_data(
    bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    resource_id: str | None = None,
    original_msg_id: str | None = None,
    reason_code: str | None = None,
) -> JsonType:
    """Generate a status-update callback payload for an RTP resource.

    Args:
        bic: Bank Identifier Code of the initiating service provider.
        resource_id: RTP resource identifier used as the default original message ID.
        original_msg_id: Original RTP resource identifier, when different from ``resource_id``.
        reason_code: Optional EPC 4.0 status reason code.
    """
    resource_id = resource_id or str(uuid.uuid4())
    original_msg_id = original_msg_id or resource_id
    transaction_info: dict[str, JsonType] = {}

    if reason_code is not None:
        transaction_info["StsRsnInf"] = [{"Rsn": {"Cd": reason_code}}]

    return {
        "SepaRequestToPayStatusUpdateResponseResource": {
            "Document": {
                "CdtrPmtActvtnReqStsRpt": {
                    "GrpHdr": {
                        "MsgId": str(uuid.uuid4()),
                        "CreDtTm": generate_create_time(),
                        "InitgPty": {"Id": {"OrgId": {"AnyBIC": bic}}},
                    },
                    "OrgnlGrpInfAndSts": {
                        "OrgnlMsgId": original_msg_id,
                        "OrgnlMsgNmId": "pain.013.001.07",
                        "OrgnlCreDtTm": generate_create_time(),
                    },
                    "OrgnlPmtInfAndSts": [
                        {
                            "OrgnlPmtInfId": str(uuid.uuid4()),
                            "TxInfAndSts": [transaction_info],
                        }
                    ],
                }
            }
        }
    }
