from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_session_token, get_bearer_token
from app.db.session import get_db_session
from app.repositories.users import UserRepository


async def get_current_user(
    token: str = Depends(get_bearer_token), session: AsyncSession = Depends(get_db_session)
):
    principal = decode_session_token(token)
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(principal.telegram_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user


async def get_admin_user(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для администраторов")
    return user

