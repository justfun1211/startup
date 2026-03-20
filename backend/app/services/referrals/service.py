from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import CreditReason, ReferralStatus
from app.models.user import Referral, User
from app.services.credits.service import CreditsService
from app.services.events import track_event
from app.utils.time import utcnow


class ReferralService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.credits = CreditsService(session)

    async def attach_referrer(self, invitee: User, referral_code: str | None) -> Referral | None:
        if not referral_code or invitee.referred_by_user_id:
            return None

        inviter = await self._get_user_by_referral_code(referral_code)
        if inviter is None or inviter.id == invitee.id:
            return None

        now = utcnow()
        referral = Referral(
            inviter_user_id=inviter.id,
            invitee_user_id=invitee.id,
            referral_code=referral_code,
            status=ReferralStatus.REWARDED,
            inviter_bonus_requests=self.settings.referral_bonus_inviter,
            invitee_bonus_requests=self.settings.referral_bonus_invitee,
            qualified_at=now,
            rewarded_at=now,
        )
        invitee.referred_by_user_id = inviter.id
        self.session.add(referral)

        await self.credits.grant(
            invitee.id,
            self.settings.referral_bonus_invitee,
            CreditReason.REFERRAL_BONUS_INVITEE,
            "referral",
            str(referral.id),
            "Бонус приглашенному пользователю",
        )
        await self.credits.grant(
            inviter.id,
            self.settings.referral_bonus_inviter,
            CreditReason.REFERRAL_BONUS_INVITER,
            "referral",
            str(referral.id),
            "Бонус пригласившему пользователю",
        )

        await track_event(self.session, invitee.id, "referral_clicked", {"referral_code": referral_code})
        await track_event(self.session, inviter.id, "referral_rewarded", {"invitee_user_id": str(invitee.id)})
        return referral

    async def reward_inviter_for_first_success(self, invitee: User) -> Referral | None:
        if not invitee.referred_by_user_id:
            return None

        result = await self.session.execute(select(Referral).where(Referral.invitee_user_id == invitee.id))
        referral = result.scalar_one_or_none()
        if referral is None:
            return None
        return referral

    async def stats_for_user(self, user: User) -> dict:
        result = await self.session.execute(select(Referral).where(Referral.inviter_user_id == user.id))
        referrals = list(result.scalars().all())
        rewarded = [item for item in referrals if item.status == ReferralStatus.REWARDED]
        return {
            "invited_count": len(referrals),
            "rewarded_count": len(rewarded),
            "total_bonus_requests": sum(item.inviter_bonus_requests for item in rewarded),
            "invitee_bonus_requests": self.settings.referral_bonus_invitee,
            "inviter_bonus_requests": self.settings.referral_bonus_inviter,
        }

    async def _get_user_by_referral_code(self, referral_code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == referral_code))
        return result.scalar_one_or_none()
