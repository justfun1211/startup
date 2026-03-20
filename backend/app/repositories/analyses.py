import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AnalysisStatus
from app.models.analysis import AnalysisRun, Report


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, analysis_id: uuid.UUID) -> AnalysisRun | None:
        return await self.session.get(AnalysisRun, analysis_id)

    async def list_for_user(self, user_id: uuid.UUID, limit: int = 20) -> list[AnalysisRun]:
        result = await self.session.execute(
            select(AnalysisRun)
            .where(AnalysisRun.user_id == user_id)
            .order_by(desc(AnalysisRun.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_report(self, analysis_id: uuid.UUID) -> Report | None:
        result = await self.session.execute(select(Report).where(Report.analysis_run_id == analysis_id))
        return result.scalar_one_or_none()

    async def active_count(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(AnalysisRun).where(
                AnalysisRun.user_id == user_id,
                AnalysisRun.status.in_([AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING]),
            )
        )
        return len(list(result.scalars().all()))

