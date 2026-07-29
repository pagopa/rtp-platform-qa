"""Utility to generate DS-12P positive (CNCL) RFC callback payloads for v2 callback tests.

The generated payload mimics the v2 callback sent for a SEPA Request-to-Pay
Cancellation Response with a CNCL (Cancelled As Per Request) status,
indicating that the cancellation request has been accepted and the RTP
is cancelled.
"""

import uuid

from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.datetime_utils import generate_create_time, generate_execution_date
from utils.type_utils import JsonType

CNCL_STATUS = "CNCL"
INVALID_STATUS = "INVALID"
ACCR_TX_CXL_STATUS = "ACCR"
ASSIGNOR_BIC = "ANYBICXXXXX"


def generate_callback_data_DS_12P_positive_compliant(
    bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    resource_id: str | None = None,
    original_msg_id: str | None = None,
    assignee_bic: str | None = None,
) -> JsonType:
    """Generate a DS-12P CNCL compliant RFC callback payload (v2).

    Args:
        bic: Bank Identifier Code of the debtor agent (defaults to the
            Debtor Service Provider C id, MOCKSP05).
        resource_id: The resource ID of the RTP being cancelled (optional, generates random if not provided).
        original_msg_id: The original message ID without dashes (optional, generates random if not provided).
        assignee_bic: Bank Identifier Code of the assignee (defaults to ``bic``). Used for certificate verification.

    Returns:
        JsonType: JSON-serializable DS-12P CNCL compliant callback payload,
        ready to be used in v2 callback tests.
    """
    return _generate_rfc_callback_data_v2(
        status=CNCL_STATUS,
        bic=bic,
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic=assignee_bic,
    )


def generate_non_compliant_callback_data_DS_12P_positive(
    bic: str = DEBTOR_SERVICE_PROVIDER_C_ID,
    resource_id: str | None = None,
    original_msg_id: str | None = None,
    assignee_bic: str | None = None,
) -> JsonType:
    """Generate a DS-12P non-compliant RFC callback payload (v2).

    The payload simulates a v2 RFC callback with an invalid cancellation
    confirmation status, used to test the system's handling of non-compliant
    callbacks.

    Args:
        bic: Bank Identifier Code of the debtor agent (defaults to the
            Debtor Service Provider C id, MOCKSP05).
        resource_id: The resource ID of the RTP being cancelled (optional, generates random if not provided).
        original_msg_id: The original message ID without dashes (optional, generates random if not provided).
        assignee_bic: Bank Identifier Code of the assignee (defaults to ``bic``). Used for certificate verification.

    Returns:
        JsonType: JSON-serializable DS-12P callback payload with invalid
        status, ready to be used in v2 callback tests.
    """
    return _generate_rfc_callback_data_v2(
        status=INVALID_STATUS,
        bic=bic,
        resource_id=resource_id,
        original_msg_id=original_msg_id,
        assignee_bic=assignee_bic,
    )


def _generate_rfc_callback_data_v2(
    status: str,
    bic: str,
    resource_id: str | None,
    original_msg_id: str | None,
    assignee_bic: str | None,
) -> JsonType:
    if assignee_bic is None:
        assignee_bic = bic

    resource_id = resource_id if resource_id else str(uuid.uuid4())
    message_id = original_msg_id if original_msg_id else resource_id.replace("-", "")

    case_id = f"CASE-{uuid.uuid4()}"
    cxl_sts_id = f"CXLSTS-{uuid.uuid4()}"
    instr_id = f"INSTR-{uuid.uuid4()}"
    end_to_end_id = f"E2E-{uuid.uuid4()}"

    create_time = generate_create_time()
    execution_date = generate_execution_date(1, 15)

    amount = 150.00

    return {
        "resourceId": resource_id,
        "SepaRequestToPayCancellationResponse": {
            "Document": {
                "RsltnOfInvstgtn": {
                    "Assgnmt": {
                        "Id": case_id,
                        "Assgnr": {"Pty": {"Id": {"OrgId": {"AnyBIC": ASSIGNOR_BIC}}}},
                        "Assgne": {"Agt": {"FinInstnId": {"BICFI": assignee_bic}}},
                        "CreDtTm": create_time,
                    },
                    "Sts": {"Conf": status},
                    "CxlDtls": {
                        "TxInfAndSts": [
                            {
                                "CxlStsId": cxl_sts_id,
                                "OrgnlGrpInf": {
                                    "OrgnlMsgId": message_id,
                                    "OrgnlMsgNmId": "pain.013.001.11",
                                    "OrgnlCreDtTm": create_time,
                                },
                                "OrgnlInstrId": instr_id,
                                "OrgnlEndToEndId": end_to_end_id,
                                "TxCxlSts": ACCR_TX_CXL_STATUS,
                                "CxlStsRsnInf": {"Orgtr": {"Id": {"OrgId": {"AnyBIC": bic}}}},
                                "OrgnlTxRef": {
                                    "Amt": {"InstdAmt": amount},
                                    "ReqdExctnDt": {"Dt": execution_date},
                                    "PmtTpInf": {"SvcLvl": {"Cd": "SRTP"}, "LclInstrm": {"Cd": "INST"}},
                                    "DbtrAgt": {"FinInstnId": {"BICFI": bic}},
                                    "CdtrAgt": {"FinInstnId": {"BICFI": ASSIGNOR_BIC}},
                                    "Cdtr": {
                                        "Pty": {"Nm": "Acme Merchant Srl", "Id": {"OrgId": {"AnyBIC": ASSIGNOR_BIC}}}
                                    },
                                    "CdtrAcct": {"Id": {"IBAN": "IT60X0542811101000000123456"}},
                                },
                            }
                        ]
                    },
                }
            }
        },
        "_links": {
            "initialSepaRequestToPayUri": {
                "href": f"https://api.example.com/srtp/requests-to-pay/{resource_id}",
                "templated": False,
            }
        },
    }
