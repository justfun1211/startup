from app.core.constants import CreditReason
from app.services.credits.service import CreditsService
from app.services.users import UserService


async def test_new_user_gets_free_requests_only_once(session):
    service = UserService(session)
    payload = {"id": 777, "first_name": "Иван", "username": "ivan"}
    user, created = await service.get_or_create_telegram_user(payload)
    await session.commit()
    assert created is True
    balance = await CreditsService(session).get_or_create_balance(user.id)
    assert balance.available_requests == 10

    same_user, created_again = await service.get_or_create_telegram_user(payload)
    await session.commit()
    assert created_again is False
    same_balance = await CreditsService(session).get_or_create_balance(same_user.id)
    assert same_balance.available_requests == 10

