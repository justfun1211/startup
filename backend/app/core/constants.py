from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class AnalysisSource(StrEnum):
    BOT = "bot"
    TWA = "twa"
    ADMIN_TEST = "admin_test"


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CreditReason(StrEnum):
    INITIAL_FREE_BONUS = "initial_free_bonus"
    REFERRAL_BONUS_INVITER = "referral_bonus_inviter"
    REFERRAL_BONUS_INVITEE = "referral_bonus_invitee"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    ANALYSIS_DEBIT = "analysis_debit"
    ANALYSIS_REFUND = "analysis_refund"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class PaymentProvider(StrEnum):
    TELEGRAM_STARS = "telegram_stars"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PRE_CHECKOUT = "pre_checkout"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class ReferralStatus(StrEnum):
    CLICKED = "clicked"
    STARTED = "started"
    QUALIFIED = "qualified"
    REWARDED = "rewarded"
    REJECTED = "rejected"


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BroadcastImageMode(StrEnum):
    NONE = "none"
    PHOTO = "photo"


class BroadcastDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"

