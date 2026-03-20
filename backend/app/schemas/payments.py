import uuid
from datetime import datetime

from pydantic import BaseModel


class PaymentPackSchema(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    description: str
    stars_amount: int
    requests_amount: int
    is_active: bool
    sort_order: int


class PaymentIntentSchema(BaseModel):
    pack_code: str


class PaymentSchema(BaseModel):
    id: uuid.UUID
    invoice_payload: str
    amount_xtr: int
    requests_amount: int
    status: str
    created_at: datetime
    paid_at: datetime | None = None


class PaymentInvoiceResponse(BaseModel):
    message: str
    invoice_payload: str
    amount_xtr: int
    requests_amount: int
