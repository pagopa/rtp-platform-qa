from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RTPOperationCode(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class PaymentPositionStatus(str, Enum):
    VALID = "VALID"
    PARTIALLY_VALID = "PARTIALLY_VALID"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class RTPMessage(BaseModel):
    id: int = Field(..., gt=0)
    operation: RTPOperationCode
    timestamp: int = Field(..., ge=0)
    iuv: str | None = Field(None, min_length=1, max_length=35)
    subject: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1024)
    ec_tax_code: str | None = Field(None, min_length=11, max_length=16)
    debtor_tax_code: str | None = Field(None, min_length=11, max_length=16)
    nav: str | None = Field(None, max_length=64)
    due_date: int | None = Field(None, ge=0)
    amount: int | None = Field(None, ge=0)
    status: PaymentPositionStatus | None = None
    psp_code: str | None = Field(None, max_length=32)
    psp_tax_code: str | None = Field(None, min_length=11, max_length=16)
    is_partial_payment: bool | None = None

    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)


class SendStatus(BaseModel):
    status: Literal["success"]


class FileError(BaseModel):
    type: str
    message: str


class FileSendResult(BaseModel):
    sent: int
    failed: int
    errors: list[FileError]
