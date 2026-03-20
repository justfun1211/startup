from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditReason
from app.models.billing import CreditLedger, UserBalance


class CreditsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_balance(self, user_id) -> UserBalance:
        balance = await self.session.get(UserBalance, user_id)
        if balance is None:
            balance = UserBalance(user_id=user_id, available_requests=0, reserved_requests=0)
            self.session.add(balance)
            await self.session.flush()
        return balance

    async def grant(
        self,
        user_id,
        requests: int,
        reason: CreditReason,
        reference_type: str | None = None,
        reference_id: str | None = None,
        comment: str | None = None,
    ) -> UserBalance:
        balance = await self.get_or_create_balance(user_id)
        balance.available_requests += requests
        await self._write_ledger(user_id, requests, balance.available_requests, reason, reference_type, reference_id, comment)
        await self.session.flush()
        return balance

    async def reserve_for_analysis(self, user_id, analysis_id: str) -> UserBalance:
        balance = await self.get_or_create_balance(user_id)
        if balance.available_requests < 1:
            raise ValueError("Недостаточно запросов")
        balance.available_requests -= 1
        balance.reserved_requests += 1
        await self._write_ledger(
            user_id,
            -1,
            balance.available_requests,
            CreditReason.ANALYSIS_DEBIT,
            "analysis_run",
            analysis_id,
            "Резерв запроса на анализ",
        )
        await self.session.flush()
        return balance

    async def commit_reserved_analysis(self, user_id) -> UserBalance:
        balance = await self.get_or_create_balance(user_id)
        if balance.reserved_requests > 0:
            balance.reserved_requests -= 1
        await self.session.flush()
        return balance

    async def refund_reserved_analysis(self, user_id, analysis_id: str, comment: str | None = None) -> UserBalance:
        balance = await self.get_or_create_balance(user_id)
        if balance.reserved_requests > 0:
            balance.reserved_requests -= 1
        balance.available_requests += 1
        await self._write_ledger(
            user_id,
            1,
            balance.available_requests,
            CreditReason.ANALYSIS_REFUND,
            "analysis_run",
            analysis_id,
            comment or "Возврат за неуспешный анализ",
        )
        await self.session.flush()
        return balance

    async def _write_ledger(
        self,
        user_id,
        delta_requests: int,
        balance_after: int,
        reason: CreditReason,
        reference_type: str | None,
        reference_id: str | None,
        comment: str | None,
    ) -> None:
        self.session.add(
            CreditLedger(
                user_id=user_id,
                delta_requests=delta_requests,
                balance_after=balance_after,
                reason=reason,
                reference_type=reference_type,
                reference_id=reference_id,
                comment=comment,
            )
        )

    async def total_bonus_by_reason(self, user_id, reason: CreditReason) -> int:
        result = await self.session.execute(
            select(CreditLedger).where(CreditLedger.user_id == user_id, CreditLedger.reason == reason)
        )
        return sum(item.delta_requests for item in result.scalars().all())

