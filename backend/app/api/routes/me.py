from fastapi import APIRouter, Depends, Header, HTTPException, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import decode_session_token
from app.repositories.users import UserRepository
from app.db.session import get_db_session
from app.schemas.analysis import AnalysisCreateSchema, AnalysisDetailSchema, AnalysisListItemSchema
from app.schemas.common import MessageResponse
from app.schemas.referrals import ReferralMeSchema
from app.schemas.user import BalanceSchema, UserContextSchema
from app.services.analysis_service import AnalysisService
from app.services.credits.service import CreditsService
from app.services.referrals.service import ReferralService
from app.core.queue import get_arq_pool
from app.schemas.payments import PaymentPackSchema

router = APIRouter(prefix="/api", tags=["user"])


@router.get("/me", response_model=UserContextSchema)
async def get_me(user=Depends(get_current_user)):
    return UserContextSchema(
        id=str(user.id),
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.is_admin,
        referral_code=user.referral_code,
        created_at=user.created_at,
    )


@router.get("/me/balance", response_model=BalanceSchema)
async def get_balance(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    balance = await CreditsService(session).get_or_create_balance(user.id)
    return BalanceSchema(available_requests=balance.available_requests, reserved_requests=balance.reserved_requests)


@router.get("/reports", response_model=list[AnalysisListItemSchema])
async def get_reports(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await AnalysisService(session).list_reports(user.id)


@router.get("/reports/{report_id}", response_model=AnalysisDetailSchema)
async def get_report(report_id: str, user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    detail = await AnalysisService(session).get_detail(user.id, UUID(report_id), is_admin=user.is_admin)
    if detail is None:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    return detail


@router.post("/reports", response_model=MessageResponse)
async def create_report(
    payload: AnalysisCreateSchema, user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)
):
    service = AnalysisService(session)
    balance = await CreditsService(session).get_or_create_balance(user.id)
    if balance.available_requests < 1:
        raise HTTPException(status_code=402, detail="Запросы закончились. Откройте экран тарифов.")
    try:
        await service.enqueue_analysis(user, payload, await get_arq_pool())
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageResponse(message="Идея принята в работу. Когда отчет будет готов, мы пришлем уведомление в боте.")


@router.get("/reports/{report_id}/pdf")
async def get_report_pdf(
    report_id: str,
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    session_token = token
    if not session_token and authorization and authorization.startswith("Bearer "):
        session_token = authorization.removeprefix("Bearer ").strip()
    if not session_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    principal = decode_session_token(session_token)
    user = await UserRepository(session).get_by_telegram_id(principal.telegram_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    report_uuid = UUID(report_id)
    detail = await AnalysisService(session).get_detail(user.id, report_uuid, is_admin=user.is_admin)
    if detail is None or detail.pdf_url is None:
        raise HTTPException(status_code=404, detail="PDF недоступен")
    from fastapi.responses import FileResponse
    from app.models.analysis import AnalysisRun

    analysis = await session.get(AnalysisRun, report_uuid)
    return FileResponse(path=analysis.pdf_path, filename=f"report-{report_id}.pdf", media_type="application/pdf")


@router.get("/pricing/packs", response_model=list[PaymentPackSchema])
async def pricing_packs(session: AsyncSession = Depends(get_db_session)):
    from app.services.payments.service import PaymentsService

    packs = await PaymentsService(session).list_packs()
    return [
        PaymentPackSchema(
            id=item.id,
            code=item.code,
            title=item.title,
            description=item.description,
            stars_amount=item.stars_amount,
            requests_amount=item.requests_amount,
            is_active=item.is_active,
            sort_order=item.sort_order,
        )
        for item in packs
    ]


@router.get("/referrals/me", response_model=ReferralMeSchema)
async def referrals_me(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    stats = await ReferralService(session).stats_for_user(user)
    from app.core.config import get_settings

    settings = get_settings()
    return ReferralMeSchema(
        referral_link=f"https://t.me/{settings.bot_username}?start=ref_{user.referral_code}",
        referral_code=user.referral_code,
        **stats,
    )
