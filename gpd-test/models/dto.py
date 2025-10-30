from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class RTPOperationCode(str, Enum):
  CREATE = 'CREATE'
  UPDATE = 'UPDATE'
  DELETE = 'DELETE'

class PaymentPositionStatus(str, Enum):
  VALID = 'VALID'
  PARTIALLY_VALID = 'PARTIALLY_VALID'
  PAID = 'PAID'
  EXPIRED = 'EXPIRED'
  INVALID = 'INVALID'
  DRAFT = 'DRAFT'
  PUBLISHED = 'PUBLISHED'

class RTPMessage(BaseModel):
  id: int = Field(..., gt=0)
  operation: RTPOperationCode
  timestamp: int = Field(..., ge=0)
  iuv: Optional[str] = Field(None, min_length=1, max_length=35)
  subject: Optional[str] = Field(None, max_length=255)
  description: Optional[str] = Field(None, max_length=1024)
  ec_tax_code: Optional[str] = Field(None, min_length=11, max_length=16)
  debtor_tax_code: Optional[str] = Field(None, min_length=11, max_length=16)
  nav: Optional[str] = Field(None, max_length=64)
  due_date: Optional[int] = Field(None, ge=0)
  amount: Optional[int] = Field(None, ge=0)
  status: Optional[PaymentPositionStatus] = None
  psp_code: Optional[str] = Field(None, max_length=32)
  psp_tax_code: Optional[str] = Field(None, min_length=11, max_length=16)
  is_partial_payment: Optional[bool] = None

  class Config:
    anystr_strip_whitespace = True
    use_enum_values = True

class SendStatus(BaseModel):
  status: Literal['success']

class FileError(BaseModel):
  type: str
  message: str

class FileSendResult(BaseModel):
  sent: int
  failed: int
  errors: List[FileError]