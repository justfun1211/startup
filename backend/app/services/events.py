from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserEvent


async def track_event(session: AsyncSession, user_id, event_name: str, payload: dict | None = None) -> None:
    session.add(UserEvent(user_id=user_id, event_name=event_name, event_json=payload or {}))

