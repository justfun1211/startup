import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CreditReason, PaymentProvider, PaymentStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserBalance(Base):
    __tablename__ = "user_balances"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    available_requests: Mapped[int] = mapped_column(Integer, default=0)
    reserved_requests: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="balance")


class CreditLedger(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "credit_ledger"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    delta_requests: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[CreditReason] = mapped_column(
        Enum(CreditReason, values_callable=lambda enum: [item.value for item in enum], native_enum=False)
    )
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentPack(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payment_packs"

    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    stars_amount: Mapped[int] = mapped_column(Integer)
    requests_amount: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Payment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_user_id_created_at", "user_id", "created_at"),
        UniqueConstraint("invoice_payload", name="uq_payments_invoice_payload"),
        UniqueConstraint("telegram_payment_charge_id", name="uq_payments_telegram_payment_charge_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    pack_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_packs.id"))
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=PaymentProvider.TELEGRAM_STARS,
    )
    invoice_payload: Mapped[str] = mapped_column(String(255))
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_xtr: Mapped[int] = mapped_column(Integer)
    requests_amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=PaymentStatus.PENDING,
    )
    raw_update_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
