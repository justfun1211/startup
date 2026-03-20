import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.billing import UserBalance
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as test_session:
        yield test_session
    await engine.dispose()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        telegram_id=123456,
        username="tester",
        first_name="Тест",
        last_name=None,
        language_code="ru",
        is_admin=False,
        referral_code="REFTEST01",
    )
    session.add(user)
    await session.flush()
    session.add(UserBalance(user_id=user.id, available_requests=10, reserved_requests=0))
    await session.commit()
    return user


@pytest.fixture
async def admin_user(session: AsyncSession) -> User:
    user = User(
        telegram_id=999999,
        username="admin",
        first_name="Админ",
        last_name=None,
        language_code="ru",
        is_admin=True,
        referral_code="ADMIN001",
    )
    session.add(user)
    await session.flush()
    session.add(UserBalance(user_id=user.id, available_requests=100, reserved_requests=0))
    await session.commit()
    return user


@pytest.fixture
async def client(session: AsyncSession, test_user: User):
    async def _override_db():
        yield session

    async def _override_user():
        return test_user

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()
