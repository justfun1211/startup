from datetime import timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditReason, PaymentStatus
from app.models.analysis import AnalysisRun
from app.models.billing import Payment
from app.models.user import User, UserEvent
from app.schemas.admin import AdminOverviewSchema
from app.utils.time import utcnow


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self) -> AdminOverviewSchema:
        now = utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        dau = await self._count_distinct_users_since(day_ago)
        mau = await self._count_distinct_users_since(month_ago)
        new_users_24h = await self._count_users_since(day_ago)
        new_users_7d = await self._count_users_since(week_ago)
        analyses_24h = await self._count_analyses_since(day_ago)
        analyses_7d = await self._count_analyses_since(week_ago)
        analyses_30d = await self._count_analyses_since(month_ago)
        payments_24h, stars_24h = await self._payment_stats(day_ago)
        payments_7d, stars_7d = await self._payment_stats(week_ago)
        payments_30d, stars_30d = await self._payment_stats(month_ago)

        referral_rewards_30d = await self._count_events_since("referral_rewarded", month_ago)
        paying_users = await self._count_paid_users()
        total_users = max(await self._count_users_since(None), 1)
        conversion = round((paying_users / total_users) * 100, 2)

        return AdminOverviewSchema(
            dau=dau,
            mau=mau,
            new_users_24h=new_users_24h,
            new_users_7d=new_users_7d,
            analyses_24h=analyses_24h,
            analyses_7d=analyses_7d,
            analyses_30d=analyses_30d,
            payments_24h=payments_24h,
            payments_7d=payments_7d,
            payments_30d=payments_30d,
            stars_24h=stars_24h,
            stars_7d=stars_7d,
            stars_30d=stars_30d,
            referral_rewards_30d=referral_rewards_30d,
            conversion_to_payment=conversion,
        )

    async def _count_distinct_users_since(self, since):
        stmt = select(func.count(distinct(UserEvent.user_id)))
        if since:
            stmt = stmt.where(UserEvent.created_at >= since)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def _count_users_since(self, since):
        stmt = select(func.count(User.id))
        if since:
            stmt = stmt.where(User.created_at >= since)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def _count_analyses_since(self, since):
        result = await self.session.execute(select(func.count(AnalysisRun.id)).where(AnalysisRun.created_at >= since))
        return int(result.scalar() or 0)

    async def _payment_stats(self, since):
        result = await self.session.execute(
            select(func.count(Payment.id), func.coalesce(func.sum(Payment.amount_xtr), 0)).where(
                Payment.created_at >= since, Payment.status == PaymentStatus.PAID
            )
        )
        row = result.one()
        return int(row[0] or 0), int(row[1] or 0)

    async def _count_events_since(self, event_name: str, since):
        result = await self.session.execute(
            select(func.count(UserEvent.id)).where(UserEvent.event_name == event_name, UserEvent.created_at >= since)
        )
        return int(result.scalar() or 0)

    async def _count_paid_users(self):
        result = await self.session.execute(
            select(func.count(distinct(Payment.user_id))).where(Payment.status == PaymentStatus.PAID)
        )
        return int(result.scalar() or 0)

