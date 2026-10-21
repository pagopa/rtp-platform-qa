"""Build the camt.029 cancellation status-update body for an RTP resource."""

import uuid
from dataclasses import dataclass, field

from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.datetime_utils import generate_create_time
from utils.type_utils import JsonType


@dataclass(frozen=True)
class StatusUpdateCancelBody:
    """Body of the status-update cancel callback.

    Args:
        resource_id: RTP resource identifier, with dashes.
        bic: BIC of the service provider. Defaults to the Debtor SP C BIC.
        reason_code: EPC cancellation reason code (AEXR, RCAR, RCNR or RCPR). Omitted when None.
        cancel_status_id: Cancellation status identifier. Random if omitted.
        original_created_at: Creation time of the original message. Current time if omitted.
        end_to_end_id: End-to-end identifier of the RTP.
    """

    resource_id: str
    bic: str = DEBTOR_SERVICE_PROVIDER_C_ID
    reason_code: str | None = "AEXR"
    cancel_status_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    original_created_at: str = field(default_factory=generate_create_time)
    end_to_end_id: str = "302000000000000000"

    @classmethod
    def from_resource(
        cls, resource_id: str, reason_code: str | None, bic: str = DEBTOR_SERVICE_PROVIDER_C_ID
    ) -> "StatusUpdateCancelBody":
        return cls(resource_id=resource_id, reason_code=reason_code, bic=bic)

    @property
    def resource_id_no_dashes(self) -> str:
        return self.resource_id.replace("-", "")

    def _reason_code_block(self) -> JsonType:
        if self.reason_code is None:
            return {}
        return {"CxlStsRsnInf": {"Rsn": {"Cd": self.reason_code}}}

    def to_dict(self) -> JsonType:
        reason_block = self._reason_code_block()
        return {
            "resourceId": self.resource_id,
            "Document": {
                "RsltnOfInvstgtn": {
                    "Assgnmt": {
                        "Assgne": {"Agt": {"FinInstnId": {"BICFI": self.bic}}},
                    },
                    "CxlDtls": {
                        "TxInfAndSts": [
                            {
                                "CxlStsId": self.cancel_status_id,
                                "OrgnlGrpInf": {
                                    "OrgnlMsgId": self.resource_id_no_dashes,
                                    "OrgnlMsgNmId": "camt.055.001.08",
                                    "OrgnlCreDtTm": self.original_created_at,
                                },
                                "OrgnlInstrId": self.resource_id_no_dashes,
                                "OrgnlEndToEndId": self.end_to_end_id,
                                **reason_block,
                            }
                        ]
                    },
                }
            },
        }
