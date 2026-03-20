from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditReason, PaymentProvider, PaymentStatus
from app.models.billing import Payment, PaymentPack
from app.models.user import User
from app.repositories.payments import PaymentRepository
from app.services.credits.service import CreditsService
from app.services.events import track_event
from app.utils.ids import generate_invoice_payload
from app.utils.time import utcnow


@dataclass
class PaymentIntent:
    payment: Payment
    pack: PaymentPack


class PaymentsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.credits = CreditsService(session)

    async def list_packs(self) -> list[PaymentPack]:
        return await self.repo.list_active_packs()

    async def create_payment_intent(self, user: User, pack_code: str) -> PaymentIntent:
        pack = await self.repo.get_pack_by_code(pack_code)
        if pack is None:
            raise ValueError("Пакет не найден")
        payment = Payment(
            user_id=user.id,
            pack_id=pack.id,
            provider=PaymentProvider.TELEGRAM_STARS,
            invoice_payload=generate_invoice_payload(user.id, pack.code),
            amount_xtr=pack.stars_amount,
            requests_amount=pack.requests_amount,
            status=PaymentStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()
        await track_event(self.session, user.id, "payment_initiated", {"payment_id": str(payment.id), "pack_code": pack.code})
        return PaymentIntent(payment=payment, pack=pack)

    async def mark_pre_checkout(self, invoice_payload: str, raw_update: dict) -> Payment:
        payment = await self.repo.get_by_payload(invoice_payload)
        if payment is None:
            raise ValueError("Платеж не найден")
        payment.status = PaymentStatus.PRE_CHECKOUT
        payment.raw_update_json = raw_update
        return payment

    async def mark_paid_once(
        self,
        invoice_payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str | None,
        raw_update: dict,
    ) -> Payment:
        payment = await self.repo.get_by_payload(invoice_payload)
        if payment is None:
            raise ValueError("Платеж не найден")
        if payment.status == PaymentStatus.PAID:
            return payment

        payment.status = PaymentStatus.PAID
        payment.telegram_payment_charge_id = telegram_payment_charge_id
        payment.provider_payment_charge_id = provider_payment_charge_id
        payment.raw_update_json = raw_update
        payment.paid_at = utcnow()
        await self.credits.grant(
            payment.user_id,
            payment.requests_amount,
            CreditReason.PURCHASE,
            "payment",
            str(payment.id),
            "Пополнение через Telegram Stars",
        )
        await track_event(self.session, payment.user_id, "payment_succeeded", {"payment_id": str(payment.id)})
        return payment

    async def get_payment(self, invoice_payload: str) -> Payment | None:
        return await self.repo.get_by_payload(invoice_payload)

