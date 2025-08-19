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
  iuv: str
  subject: str
  description: str
  ec_tax_code: str
  debtor_tax_code: str
  nav: str
  due_date: int
  amount: int
  status: PaymentPositionStatus
  psp_code: Optional[str] = None
  psp_tax_code: Optional[str] = None
  is_partial_payment: Optional[bool] = None
