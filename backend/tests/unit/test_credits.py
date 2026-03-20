from app.core.constants import CreditReason
from app.services.credits.service import CreditsService


async def test_successful_analysis_debit(session, test_user):
    service = CreditsService(session)
    balance = await service.reserve_for_analysis(test_user.id, "analysis-1")
    assert balance.available_requests == 9
    assert balance.reserved_requests == 1


async def test_failed_analysis_refund_rollback(session, test_user):
    service = CreditsService(session)
    await service.reserve_for_analysis(test_user.id, "analysis-2")
    balance = await service.refund_reserved_analysis(test_user.id, "analysis-2")
    assert balance.available_requests == 10
    assert balance.reserved_requests == 0

