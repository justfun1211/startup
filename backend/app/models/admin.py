import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import BroadcastDeliveryStatus, BroadcastImageMode, BroadcastStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AdminBroadcast(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "admin_broadcasts"

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=BroadcastStatus.DRAFT,
    )
    message_text: Mapped[str] = mapped_column(Text)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_mode: Mapped[BroadcastImageMode] = mapped_column(
        Enum(BroadcastImageMode, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=BroadcastImageMode.NONE,
    )
    target_filter_json: Mapped[dict] = mapped_column(JSON, default=dict)
    total_targets: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminBroadcastDelivery(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "admin_broadcast_deliveries"
    __table_args__ = (Index("ix_admin_broadcast_deliveries_broadcast_id_status", "broadcast_id", "status"),)

    broadcast_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_broadcasts.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[BroadcastDeliveryStatus] = mapped_column(
        Enum(BroadcastDeliveryStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=BroadcastDeliveryStatus.PENDING,
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminActionLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "admin_action_logs"

    admin_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(100))
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
