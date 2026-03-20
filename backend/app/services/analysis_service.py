import uuid

from arq import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import AnalysisSource, AnalysisStatus
from app.models.analysis import AnalysisRun, Report
from app.models.user import User
from app.repositories.analyses import AnalysisRepository
from app.schemas.analysis import AnalysisCreateSchema, AnalysisDetailSchema, AnalysisListItemSchema, AnalysisReportSchema
from app.services.credits.service import CreditsService
from app.services.events import track_event
from app.utils.summary import build_summary


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.repo = AnalysisRepository(session)
        self.credits = CreditsService(session)

    async def enqueue_analysis(self, user: User, payload: AnalysisCreateSchema, redis: ArqRedis) -> AnalysisRun:
        active = await self.repo.active_count(user.id)
        if active >= self.settings.max_active_analyses_per_user:
            raise ValueError("У вас уже есть анализ в работе. Дождитесь его завершения.")

        analysis = AnalysisRun(
            user_id=user.id,
            source=payload.source,
            input_text=payload.input_text.strip(),
            status=AnalysisStatus.QUEUED,
            prompt_version=self.settings.prompt_version,
        )
        self.session.add(analysis)
        await self.session.flush()
        await self.credits.reserve_for_analysis(user.id, str(analysis.id))
        await track_event(self.session, user.id, "idea_submitted", {"analysis_id": str(analysis.id)})
        await track_event(self.session, user.id, "analysis_queued", {"analysis_id": str(analysis.id)})
        await redis.enqueue_job("process_analysis_run", str(analysis.id))
        return analysis

    async def list_reports(self, user_id) -> list[AnalysisListItemSchema]:
        items = await self.repo.list_for_user(user_id)
        return [
            AnalysisListItemSchema(
                id=item.id,
                status=item.status,
                short_summary_text=item.short_summary_text,
                pdf_path=item.pdf_path,
                created_at=item.created_at,
                completed_at=item.completed_at,
            )
            for item in items
        ]

    async def get_detail(self, user_id, analysis_id: uuid.UUID, is_admin: bool = False) -> AnalysisDetailSchema | None:
        item = await self.repo.get(analysis_id)
        if item is None:
            return None
        if item.user_id != user_id and not is_admin:
            return None
        report = AnalysisReportSchema.model_validate(item.top_level_report_json) if item.top_level_report_json else None
        pdf_url = f"/api/reports/{item.id}/pdf" if item.pdf_path else None
        return AnalysisDetailSchema(
            id=item.id,
            source=item.source,
            input_text=item.input_text,
            status=item.status,
            top_level_report_json=report,
            short_summary_text=item.short_summary_text,
            pdf_url=pdf_url,
            model_name=item.model_name,
            prompt_version=item.prompt_version,
            tokens_input=item.tokens_input,
            tokens_output=item.tokens_output,
            total_tokens=item.total_tokens,
            cost_rub=item.cost_rub,
            latency_ms=item.latency_ms,
            created_at=item.created_at,
            completed_at=item.completed_at,
        )

    async def save_completed_report(
        self,
        analysis: AnalysisRun,
        report: AnalysisReportSchema,
        model_name: str,
        usage: dict,
        latency_ms: int,
        pdf_path: str | None,
    ) -> None:
        summary = build_summary(report)
        analysis.status = AnalysisStatus.COMPLETED
        analysis.top_level_report_json = report.model_dump(mode="json")
        analysis.short_summary_text = summary
        analysis.pdf_path = pdf_path
        analysis.model_name = model_name
        analysis.tokens_input = usage.get("prompt_tokens")
        analysis.tokens_output = usage.get("completion_tokens")
        analysis.total_tokens = usage.get("total_tokens")
        analysis.latency_ms = latency_ms
        from app.utils.time import utcnow

        analysis.completed_at = utcnow()
        self.session.add(
            Report(
                analysis_run_id=analysis.id,
                user_id=analysis.user_id,
                report_json=report.model_dump(mode="json"),
                short_summary=summary,
                pdf_path=pdf_path,
            )
        )
        await self.credits.commit_reserved_analysis(analysis.user_id)
        await track_event(self.session, analysis.user_id, "analysis_completed", {"analysis_id": str(analysis.id)})

    async def mark_failed(self, analysis: AnalysisRun, error_code: str, error_message: str) -> None:
        from app.utils.time import utcnow

        analysis.status = AnalysisStatus.FAILED
        analysis.error_code = error_code
        analysis.error_message = error_message
        analysis.completed_at = utcnow()
        await self.credits.refund_reserved_analysis(analysis.user_id, str(analysis.id))
        await track_event(self.session, analysis.user_id, "analysis_failed", {"analysis_id": str(analysis.id), "error_code": error_code})
