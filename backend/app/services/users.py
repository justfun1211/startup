from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import CreditReason
from app.models.user import User
from app.services.credits.service import CreditsService
from app.services.events import track_event
from app.utils.ids import generate_referral_code
from app.utils.time import utcnow


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.credits = CreditsService(session)

    async def get_or_create_telegram_user(self, telegram_user: dict) -> tuple[User, bool]:
        from app.repositories.users import UserRepository

        repo = UserRepository(self.session)
        user = await repo.get_by_telegram_id(int(telegram_user["id"]))
        is_new = user is None
        if user is None:
            user = User(
                telegram_id=int(telegram_user["id"]),
                username=telegram_user.get("username"),
                first_name=telegram_user.get("first_name") or "Пользователь",
                last_name=telegram_user.get("last_name"),
                language_code=telegram_user.get("language_code"),
                is_admin=int(telegram_user["id"]) in self.settings.admin_ids,
                referral_code=generate_referral_code(),
                free_requests_granted=self.settings.free_requests_initial,
            )
            self.session.add(user)
            await self.session.flush()
            await self.credits.grant(
                user.id,
                self.settings.free_requests_initial,
                CreditReason.INITIAL_FREE_BONUS,
                "user",
                str(user.id),
                "Стартовый бонус при регистрации",
            )
            await track_event(self.session, user.id, "user_started", {})
        else:
            user.username = telegram_user.get("username")
            user.first_name = telegram_user.get("first_name") or user.first_name
            user.last_name = telegram_user.get("last_name")
            user.language_code = telegram_user.get("language_code")
            user.is_admin = user.telegram_id in self.settings.admin_ids

        user.last_seen_at = utcnow()
        await self.session.flush()
        return user, is_new
