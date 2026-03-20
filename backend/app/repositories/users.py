from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import UserBalance
from app.models.user import Referral, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, referral_code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == referral_code))
        return result.scalar_one_or_none()

    async def get_balance(self, user_id) -> UserBalance | None:
        return await self.session.get(UserBalance, user_id)

    async def list_referrals(self, user_id) -> list[Referral]:
        result = await self.session.execute(select(Referral).where(Referral.inviter_user_id == user_id))
        return list(result.scalars().all())

    async def query_active_users(self) -> Select[tuple[User]]:
        return select(User)

