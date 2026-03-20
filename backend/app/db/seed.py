import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.billing import PaymentPack


PACKS = [
    {
        "code": "test_1",
        "title": "1 запрос",
        "description": "Тестовый пакет для быстрой проверки оплаты в Telegram Stars.",
        "stars_amount": 10,
        "requests_amount": 1,
        "sort_order": 0,
    },
    {
        "code": "starter_15",
        "title": "15 запросов",
        "description": "Подходит для первых проверок гипотез и нескольких итераций идеи.",
        "stars_amount": 150,
        "requests_amount": 15,
        "sort_order": 1,
    },
    {
        "code": "growth_50",
        "title": "50 запросов",
        "description": "Для активной проработки нескольких направлений и запуска MVP.",
        "stars_amount": 420,
        "requests_amount": 50,
        "sort_order": 2,
    },
    {
        "code": "scale_120",
        "title": "120 запросов",
        "description": "Для команд, агентств и серийной проверки стартап-гипотез.",
        "stars_amount": 900,
        "requests_amount": 120,
        "sort_order": 3,
    },
]


async def seed() -> None:
    async with SessionLocal() as session:
        for pack_data in PACKS:
            result = await session.execute(select(PaymentPack).where(PaymentPack.code == pack_data["code"]))
            pack = result.scalar_one_or_none()
            if pack is None:
                session.add(PaymentPack(**pack_data))
            else:
                for key, value in pack_data.items():
                    setattr(pack, key, value)
                pack.is_active = True
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
