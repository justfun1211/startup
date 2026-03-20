from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Payment, PaymentPack


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_pack_by_code(self, code: str) -> PaymentPack | None:
        result = await self.session.execute(select(PaymentPack).where(PaymentPack.code == code, PaymentPack.is_active.is_(True)))
        return result.scalar_one_or_none()

    async def list_active_packs(self) -> list[PaymentPack]:
        result = await self.session.execute(
            select(PaymentPack).where(PaymentPack.is_active.is_(True)).order_by(PaymentPack.sort_order.asc())
        )
        return list(result.scalars().all())

    async def get_by_payload(self, invoice_payload: str) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.invoice_payload == invoice_payload))
        return result.scalar_one_or_none()

