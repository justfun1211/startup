import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdminOverviewSchema(BaseModel):
    dau: int
    mau: int
    new_users_24h: int
    new_users_7d: int
    analyses_24h: int
    analyses_7d: int
    analyses_30d: int
    payments_24h: int
    payments_7d: int
    payments_30d: int
    stars_24h: int
    stars_7d: int
    stars_30d: int
    referral_rewards_30d: int
    conversion_to_payment: float


class AdminGrantSchema(BaseModel):
    requests: int = Field(ge=1, le=1000)
    comment: str | None = Field(default=None, max_length=500)


class AdminUserSchema(BaseModel):
    telegram_id: int
    first_name: str
    username: str | None
    is_admin: bool
    available_requests: int
    reserved_requests: int


class AdminRecentUserSchema(BaseModel):
    telegram_id: int
    first_name: str
    username: str | None
    is_admin: bool
    available_requests: int
    reserved_requests: int
    created_at: datetime
    last_seen_at: datetime


class AdminActionLogSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    admin_telegram_id: int | None
    target_telegram_id: int | None
    payload_json: dict
    created_at: datetime


class BroadcastCreateSchema(BaseModel):
    message_text: str = Field(min_length=1, max_length=4000)
    telegram_file_id: str | None = Field(default=None, max_length=255)
    dry_run: bool = False


class BroadcastSchema(BaseModel):
    id: uuid.UUID
    status: str
    message_text: str
    telegram_file_id: str | None
    total_targets: int
    success_count: int
    failure_count: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
