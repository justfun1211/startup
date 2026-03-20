from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import issue_session_token, validate_telegram_init_data
from app.db.session import get_db_session
from app.schemas.user import BalanceSchema, TwaAuthResponseSchema, TwaValidateSchema, UserContextSchema
from app.services.users import UserService
from app.services.referrals.service import ReferralService
from app.services.credits.service import CreditsService

router = APIRouter(prefix="/api/twa", tags=["twa"])


@router.post("/auth/validate", response_model=TwaAuthResponseSchema)
async def validate_twa_auth(payload: TwaValidateSchema, session: AsyncSession = Depends(get_db_session)):
    telegram_user = validate_telegram_init_data(payload.init_data_raw)
    user_service = UserService(session)
    user, _ = await user_service.get_or_create_telegram_user(telegram_user)
    await session.commit()
    balance = await CreditsService(session).get_or_create_balance(user.id)
    return TwaAuthResponseSchema(
        token=issue_session_token(user.telegram_id),
        user=UserContextSchema(
            id=str(user.id),
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            referral_code=user.referral_code,
            created_at=user.created_at,
        ),
        balance=BalanceSchema(available_requests=balance.available_requests, reserved_requests=balance.reserved_requests),
    )

