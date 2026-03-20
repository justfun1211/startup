import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.admin import AdminActionLog, AdminBroadcast
from app.models.billing import UserBalance
from app.models.user import User


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_broadcasts(self) -> list[AdminBroadcast]:
        result = await self.session.execute(select(AdminBroadcast).order_by(desc(AdminBroadcast.created_at)))
        return list(result.scalars().all())

    async def get_broadcast(self, broadcast_id: uuid.UUID) -> AdminBroadcast | None:
        return await self.session.get(AdminBroadcast, broadcast_id)

    async def list_recent_users(self, limit: int = 8):
        result = await self.session.execute(
            select(User, UserBalance)
            .outerjoin(UserBalance, UserBalance.user_id == User.id)
            .order_by(desc(User.created_at))
            .limit(limit)
        )
        return list(result.all())

    async def list_action_logs(self, limit: int = 12):
        admin_user = aliased(User)
        target_user = aliased(User)
        result = await self.session.execute(
            select(AdminActionLog, admin_user.telegram_id, target_user.telegram_id)
            .outerjoin(admin_user, admin_user.id == AdminActionLog.admin_user_id)
            .outerjoin(target_user, target_user.id == AdminActionLog.target_user_id)
            .order_by(desc(AdminActionLog.created_at))
            .limit(limit)
        )
        return list(result.all())
