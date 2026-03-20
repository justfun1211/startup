"""initial schema

Revision ID: 20260320_0001
Revises:
Create Date: 2026-03-20 03:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260320_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_status = sa.Enum("active", "blocked", name="userstatus", native_enum=False)
    analysis_source = sa.Enum("bot", "twa", "admin_test", name="analysissource", native_enum=False)
    analysis_status = sa.Enum("queued", "processing", "completed", "failed", "cancelled", name="analysisstatus", native_enum=False)
    credit_reason = sa.Enum(
        "initial_free_bonus",
        "referral_bonus_inviter",
        "referral_bonus_invitee",
        "purchase",
        "admin_grant",
        "analysis_debit",
        "analysis_refund",
        "manual_adjustment",
        name="creditreason",
        native_enum=False,
    )
    payment_provider = sa.Enum("telegram_stars", name="paymentprovider", native_enum=False)
    payment_status = sa.Enum("pending", "pre_checkout", "paid", "refunded", "failed", name="paymentstatus", native_enum=False)
    referral_status = sa.Enum("clicked", "started", "qualified", "rewarded", "rejected", name="referralstatus", native_enum=False)
    broadcast_status = sa.Enum("draft", "scheduled", "running", "completed", "failed", "cancelled", name="broadcaststatus", native_enum=False)
    broadcast_image_mode = sa.Enum("none", "photo", name="broadcastimagemode", native_enum=False)
    broadcast_delivery_status = sa.Enum("pending", "sent", "failed", "skipped", name="broadcastdeliverystatus", native_enum=False)

    bind = op.get_bind()
    for enum in [
        user_status,
        analysis_source,
        analysis_status,
        credit_reason,
        payment_provider,
        payment_status,
        referral_status,
        broadcast_status,
        broadcast_image_mode,
        broadcast_delivery_status,
    ]:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("referral_code", sa.String(length=32), nullable=False),
        sa.Column("referred_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", user_status, nullable=False, server_default="active"),
        sa.Column("free_requests_granted", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"])

    op.create_table(
        "user_balances",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True, nullable=False),
        sa.Column("available_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta_requests", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", credit_reason, nullable=False),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", sa.String(length=100), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_credit_ledger_user_id", "credit_ledger", ["user_id"])

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source", analysis_source, nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("normalized_input_json", sa.JSON(), nullable=True),
        sa.Column("status", analysis_status, nullable=False, server_default="queued"),
        sa.Column("top_level_report_json", sa.JSON(), nullable=True),
        sa.Column("short_summary_text", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=True),
        sa.Column("tokens_input", sa.Integer(), nullable=True),
        sa.Column("tokens_output", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_rub", sa.Numeric(12, 2), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_runs_user_id_created_at", "analysis_runs", ["user_id", "created_at"])
    op.create_index("ix_analysis_runs_status", "analysis_runs", ["status"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("analysis_run_id"),
    )

    op.create_table(
        "payment_packs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("requests_amount", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pack_id", sa.Uuid(), sa.ForeignKey("payment_packs.id"), nullable=False),
        sa.Column("provider", payment_provider, nullable=False, server_default="telegram_stars"),
        sa.Column("invoice_payload", sa.String(length=255), nullable=False),
        sa.Column("telegram_payment_charge_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_charge_id", sa.String(length=255), nullable=True),
        sa.Column("amount_xtr", sa.Integer(), nullable=False),
        sa.Column("requests_amount", sa.Integer(), nullable=False),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("raw_update_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("invoice_payload"),
        sa.UniqueConstraint("telegram_payment_charge_id"),
    )
    op.create_index("ix_payments_user_id_created_at", "payments", ["user_id", "created_at"])

    op.create_table(
        "referrals",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("inviter_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("invitee_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("referral_code", sa.String(length=32), nullable=False),
        sa.Column("status", referral_status, nullable=False, server_default="clicked"),
        sa.Column("inviter_bonus_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invitee_bonus_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rewarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("invitee_user_id", name="uq_referrals_invitee_user_id"),
    )
    op.create_index("ix_referrals_inviter_user_id", "referrals", ["inviter_user_id"])

    op.create_table(
        "user_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("event_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_events_event_name_created_at", "user_events", ["event_name", "created_at"])

    op.create_table(
        "admin_broadcasts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", broadcast_status, nullable=False, server_default="draft"),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=True),
        sa.Column("image_mode", broadcast_image_mode, nullable=False, server_default="none"),
        sa.Column("target_filter_json", sa.JSON(), nullable=False),
        sa.Column("total_targets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "admin_broadcast_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("broadcast_id", sa.Uuid(), sa.ForeignKey("admin_broadcasts.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", broadcast_delivery_status, nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_admin_broadcast_deliveries_broadcast_id_status",
        "admin_broadcast_deliveries",
        ["broadcast_id", "status"],
    )

    op.create_table(
        "admin_action_logs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("admin_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("admin_action_logs")
    op.drop_index("ix_admin_broadcast_deliveries_broadcast_id_status", table_name="admin_broadcast_deliveries")
    op.drop_table("admin_broadcast_deliveries")
    op.drop_table("admin_broadcasts")
    op.drop_index("ix_user_events_event_name_created_at", table_name="user_events")
    op.drop_table("user_events")
    op.drop_index("ix_referrals_inviter_user_id", table_name="referrals")
    op.drop_table("referrals")
    op.drop_index("ix_payments_user_id_created_at", table_name="payments")
    op.drop_table("payments")
    op.drop_table("payment_packs")
    op.drop_table("reports")
    op.drop_index("ix_analysis_runs_status", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_user_id_created_at", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index("ix_credit_ledger_user_id", table_name="credit_ledger")
    op.drop_table("credit_ledger")
    op.drop_table("user_balances")
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
