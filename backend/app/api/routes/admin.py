from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.core.constants import CreditReason
from app.db.session import get_db_session
from app.models.admin import AdminActionLog
from app.schemas.admin import (
    AdminActionLogSchema,
    AdminGrantSchema,
    AdminRecentUserSchema,
    AdminUserSchema,
    BroadcastCreateSchema,
    BroadcastSchema,
)
from app.services.analytics.service import AnalyticsService
from app.services.broadcasts.service import BroadcastService
from app.services.credits.service import CreditsService
from app.repositories.users import UserRepository
from app.repositories.admin import AdminRepository
from app.core.queue import get_arq_pool

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
async def get_overview(admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    service = AnalyticsService(session)
    session.add(AdminActionLog(admin_user_id=admin.id, action_type="admin_login", payload_json={}))
    await session.commit()
    return await service.overview()


@router.get("/users/{telegram_id}", response_model=AdminUserSchema)
async def get_admin_user_detail(telegram_id: int, admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    balance = await CreditsService(session).get_or_create_balance(user.id)
    return AdminUserSchema(
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        username=user.username,
        is_admin=user.is_admin,
        available_requests=balance.available_requests,
        reserved_requests=balance.reserved_requests,
    )


@router.post("/users/{telegram_id}/grant")
async def grant_requests(
    telegram_id: int,
    payload: AdminGrantSchema,
    admin=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await CreditsService(session).grant(
        user.id,
        payload.requests,
        CreditReason.ADMIN_GRANT,
        "admin",
        str(admin.id),
        payload.comment,
    )
    session.add(
        AdminActionLog(
            admin_user_id=admin.id,
            action_type="grant_requests",
            target_user_id=user.id,
            payload_json={"requests": payload.requests, "comment": payload.comment},
        )
    )
    await session.commit()
    return {"message": "Запросы начислены"}


@router.post("/broadcasts")
async def create_broadcast(
    payload: BroadcastCreateSchema,
    admin=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    from app.main import get_bot

    service = BroadcastService(session, get_bot())
    broadcast = await service.create_broadcast(admin, payload.message_text, payload.telegram_file_id, payload.dry_run)
    await service.prepare_deliveries(broadcast, admin)
    session.add(
        AdminActionLog(
            admin_user_id=admin.id,
            action_type="create_broadcast",
            payload_json={
                "broadcast_id": str(broadcast.id),
                "dry_run": payload.dry_run,
                "has_image": bool(payload.telegram_file_id),
            },
        )
    )
    await session.commit()
    await (await get_arq_pool()).enqueue_job("process_broadcast", str(broadcast.id))
    return {"id": str(broadcast.id), "status": broadcast.status}


@router.get("/broadcasts", response_model=list[BroadcastSchema])
async def list_broadcasts(admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    items = await AdminRepository(session).list_broadcasts()
    return [
        BroadcastSchema(
            id=item.id,
            status=item.status,
            message_text=item.message_text,
            telegram_file_id=item.telegram_file_id,
            total_targets=item.total_targets,
            success_count=item.success_count,
            failure_count=item.failure_count,
            created_at=item.created_at,
            started_at=item.started_at,
            finished_at=item.finished_at,
        )
        for item in items
    ]


@router.get("/broadcasts/{broadcast_id}", response_model=BroadcastSchema)
async def get_broadcast(broadcast_id: str, admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    broadcast = await AdminRepository(session).get_broadcast(UUID(broadcast_id))
    if broadcast is None:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
    return BroadcastSchema(
        id=broadcast.id,
        status=broadcast.status,
        message_text=broadcast.message_text,
        telegram_file_id=broadcast.telegram_file_id,
        total_targets=broadcast.total_targets,
        success_count=broadcast.success_count,
        failure_count=broadcast.failure_count,
        created_at=broadcast.created_at,
        started_at=broadcast.started_at,
        finished_at=broadcast.finished_at,
    )


@router.get("/recent-users", response_model=list[AdminRecentUserSchema])
async def list_recent_users(admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    items = await AdminRepository(session).list_recent_users()
    return [
        AdminRecentUserSchema(
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            username=user.username,
            is_admin=user.is_admin,
            available_requests=balance.available_requests if balance else 0,
            reserved_requests=balance.reserved_requests if balance else 0,
            created_at=user.created_at,
            last_seen_at=user.last_seen_at,
        )
        for user, balance in items
    ]


@router.get("/action-logs", response_model=list[AdminActionLogSchema])
async def list_action_logs(admin=Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    items = await AdminRepository(session).list_action_logs()
    return [
        AdminActionLogSchema(
            id=log.id,
            action_type=log.action_type,
            admin_telegram_id=admin_telegram_id,
            target_telegram_id=target_telegram_id,
            payload_json=log.payload_json,
            created_at=log.created_at,
        )
        for log, admin_telegram_id, target_telegram_id in items
    ]
