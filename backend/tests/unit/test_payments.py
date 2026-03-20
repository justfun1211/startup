from app.models.billing import PaymentPack
from app.services.credits.service import CreditsService
from app.services.payments.service import PaymentsService


async def test_payment_success_credits_user_exactly_once(session, test_user):
    pack = PaymentPack(
        code="starter",
        title="Starter",
        description="desc",
        stars_amount=100,
        requests_amount=10,
        sort_order=1,
    )
    session.add(pack)
    await session.commit()

    service = PaymentsService(session)
    intent = await service.create_payment_intent(test_user, "starter")
    await session.commit()

    await service.mark_paid_once(intent.payment.invoice_payload, "tg-1", "prov-1", {})
    await session.commit()
    await service.mark_paid_once(intent.payment.invoice_payload, "tg-1", "prov-1", {})
    await session.commit()

    balance = await CreditsService(session).get_or_create_balance(test_user.id)
    assert balance.available_requests == 20

