from enum import Enum
from pydantic import BaseModel, Field

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
  ec_tax_code: str = Field(..., alias="ec_tax_code")
  debtor_tax_code: str = Field(..., alias="debtor_tax_code")
  nav: str
  due_date: int = Field(..., alias="due_date")
  amount: int
  status: PaymentPositionStatus
  psp_code: str = Field(..., alias="psp_code")
  psp_tax_code: str = Field(..., alias="psp_tax_code")
  is_partial_payment: bool = Field(..., alias="is_partial_payment")
