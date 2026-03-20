import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AnalysisSource, AnalysisStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AnalysisRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_user_id_created_at", "user_id", "created_at"),
        Index("ix_analysis_runs_status", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[AnalysisSource] = mapped_column(
        Enum(AnalysisSource, values_callable=lambda enum: [item.value for item in enum], native_enum=False)
    )
    input_text: Mapped[str] = mapped_column(Text)
    normalized_input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        default=AnalysisStatus.QUEUED,
    )
    top_level_report_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    short_summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_rub: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="analyses")


class Report(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reports"

    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    report_json: Mapped[dict] = mapped_column(JSON)
    short_summary: Mapped[str] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

from app.models.user import User
