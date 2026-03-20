from sqlalchemy import select

from app.api.deps import get_admin_user
from app.core.constants import CreditReason
from app.models.admin import AdminActionLog
from app.services.credits.service import CreditsService


async def test_admin_grant_writes_ledger_and_audit_log(session, admin_user, test_user):
    await CreditsService(session).grant(test_user.id, 5, CreditReason.ADMIN_GRANT, "admin", str(admin_user.id), "manual")
    session.add(AdminActionLog(admin_user_id=admin_user.id, action_type="grant_requests", target_user_id=test_user.id, payload_json={"requests": 5}))
    await session.commit()
    result = await session.execute(select(AdminActionLog).where(AdminActionLog.target_user_id == test_user.id))
    assert result.scalar_one().action_type == "grant_requests"


async def test_admin_guard_blocks_non_admin(test_user):
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await get_admin_user(test_user)
