import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ReferralStatus, UserStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    referred_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=UserStatus.ACTIVE,
    )
    free_requests_granted: Mapped[int] = mapped_column(Integer, default=10)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    balance: Mapped["UserBalance"] = relationship(back_populates="user", uselist=False)
    analyses: Mapped[list["AnalysisRun"]] = relationship(back_populates="user")


class Referral(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("invitee_user_id", name="uq_referrals_invitee_user_id"),
        Index("ix_referrals_inviter_user_id", "inviter_user_id"),
    )

    inviter_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    invitee_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    referral_code: Mapped[str] = mapped_column(String(32))
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=ReferralStatus.CLICKED,
    )
    inviter_bonus_requests: Mapped[int] = mapped_column(Integer, default=0)
    invitee_bonus_requests: Mapped[int] = mapped_column(Integer, default=0)
    qualified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_events"
    __table_args__ = (Index("ix_user_events_event_name_created_at", "event_name", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    event_name: Mapped[str] = mapped_column(String(100))
    event_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


from app.models.analysis import AnalysisRun
from app.models.billing import UserBalance
