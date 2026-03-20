import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminBroadcast


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_broadcasts(self) -> list[AdminBroadcast]:
        result = await self.session.execute(select(AdminBroadcast).order_by(desc(AdminBroadcast.created_at)))
        return list(result.scalars().all())

    async def get_broadcast(self, broadcast_id: uuid.UUID) -> AdminBroadcast | None:
        return await self.session.get(AdminBroadcast, broadcast_id)
