from enum import Enum
from pydantic import BaseModel
from typing import Optional

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
  id: int
  operation: RTPOperationCode
  timestamp: int
  iuv: Optional[str] = None
  subject: Optional[str] = None
  description: Optional[str] = None
  ec_tax_code: Optional[str] = None
  debtor_tax_code: Optional[str] = None
  nav: Optional[str] = None
  due_date: Optional[int] = None
  amount: Optional[int] = None
  status: Optional[PaymentPositionStatus] = None
  psp_code: Optional[str] = None
  psp_tax_code: Optional[str] = None
  is_partial_payment: Optional[bool] = None
