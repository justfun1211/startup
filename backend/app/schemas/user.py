from datetime import datetime

from pydantic import BaseModel


class UserContextSchema(BaseModel):
    id: str
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    is_admin: bool
    referral_code: str
    created_at: datetime


class BalanceSchema(BaseModel):
    available_requests: int
    reserved_requests: int


class TwaValidateSchema(BaseModel):
    init_data_raw: str


class TwaAuthResponseSchema(BaseModel):
    token: str
    user: UserContextSchema
    balance: BalanceSchema

