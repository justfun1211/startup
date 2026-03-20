from sqlalchemy import select

from app.core.config import get_settings
from app.core.constants import ReferralStatus
from app.models.user import Referral, User
from app.services.referrals.service import ReferralService


async def test_self_referral_rejected(session):
    user = User(
        telegram_id=1,
        username="self",
        first_name="Self",
        last_name=None,
        language_code="ru",
        is_admin=False,
        referral_code="SELF001",
    )
    session.add(user)
    await session.commit()

    referral = await ReferralService(session).attach_referrer(user, "SELF001")
    assert referral is None


async def test_invitee_and_inviter_rewards_idempotent(session):
    inviter = User(telegram_id=11, username="a", first_name="A", last_name=None, language_code="ru", is_admin=False, referral_code="INVITER1")
    invitee = User(telegram_id=22, username="b", first_name="B", last_name=None, language_code="ru", is_admin=False, referral_code="INVITEE1")
    session.add_all([inviter, invitee])
    await session.flush()
    from app.models.billing import UserBalance
    session.add_all([
        UserBalance(user_id=inviter.id, available_requests=0, reserved_requests=0),
        UserBalance(user_id=invitee.id, available_requests=0, reserved_requests=0),
    ])
    await session.commit()

    service = ReferralService(session)
    referral = await service.attach_referrer(invitee, inviter.referral_code)
    await session.commit()
    assert referral is not None
    assert referral.status == ReferralStatus.REWARDED
    assert referral.inviter_bonus_requests > 0
    assert referral.invitee_bonus_requests > 0
    rewarded = await service.reward_inviter_for_first_success(invitee)
    await session.commit()
    rewarded_again = await service.reward_inviter_for_first_success(invitee)
    await session.commit()
    assert rewarded.status == ReferralStatus.REWARDED
    assert rewarded_again.status == ReferralStatus.REWARDED
