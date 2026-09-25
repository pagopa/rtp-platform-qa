from dataclasses import dataclass


@dataclass(frozen=True)
class StatusUpdateRtpContext:
    resource_id: str
    reader_access_token: str
    delivery_status_access_token: str
    certificate: str
    key: str
    notice_number: str
    payee_id: str
