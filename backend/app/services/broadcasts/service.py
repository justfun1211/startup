import asyncio
import uuid

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import BroadcastDeliveryStatus, BroadcastImageMode, BroadcastStatus, UserStatus
from app.models.admin import AdminActionLog, AdminBroadcast, AdminBroadcastDelivery
from app.models.user import User
from app.services.events import track_event
from app.utils.time import utcnow


class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot
        self.settings = get_settings()

    async def create_broadcast(self, admin_user: User, message_text: str, telegram_file_id: str | None, dry_run: bool = False) -> AdminBroadcast:
        broadcast = AdminBroadcast(
            created_by_user_id=admin_user.id,
            status=BroadcastStatus.SCHEDULED,
            message_text=message_text,
            telegram_file_id=telegram_file_id,
            image_mode=BroadcastImageMode.PHOTO if telegram_file_id else BroadcastImageMode.NONE,
            target_filter_json={"dry_run": dry_run},
        )
        self.session.add(broadcast)
        await self.session.flush()
        await self.session.flush()
        await track_event(self.session, admin_user.id, "broadcast_started", {"broadcast_id": str(broadcast.id)})
        self.session.add(
            AdminActionLog(
                admin_user_id=admin_user.id,
                action_type="broadcast_create",
                payload_json={"broadcast_id": str(broadcast.id), "dry_run": dry_run},
            )
        )
        return broadcast

    async def prepare_deliveries(self, broadcast: AdminBroadcast, admin_user: User) -> None:
        if broadcast.target_filter_json.get("dry_run"):
            targets = [admin_user]
        else:
            result = await self.session.execute(select(User).where(User.status == UserStatus.ACTIVE))
            targets = list(result.scalars().all())
        broadcast.total_targets = len(targets)
        for user in targets:
            self.session.add(AdminBroadcastDelivery(broadcast_id=broadcast.id, user_id=user.id))

    async def run_broadcast(self, broadcast: AdminBroadcast) -> AdminBroadcast:
        result = await self.session.execute(
            select(AdminBroadcastDelivery, User)
            .join(User, User.id == AdminBroadcastDelivery.user_id)
            .where(AdminBroadcastDelivery.broadcast_id == broadcast.id)
        )
        broadcast.status = BroadcastStatus.RUNNING
        broadcast.started_at = utcnow()
        for delivery, user in result.all():
            try:
                if broadcast.telegram_file_id:
                    await self.bot.send_photo(chat_id=user.telegram_id, photo=broadcast.telegram_file_id, caption=broadcast.message_text)
                else:
                    await self.bot.send_message(chat_id=user.telegram_id, text=broadcast.message_text)
                delivery.status = BroadcastDeliveryStatus.SENT
                delivery.sent_at = utcnow()
                broadcast.success_count += 1
            except Exception as exc:
                delivery.status = BroadcastDeliveryStatus.FAILED
                delivery.error_code = exc.__class__.__name__
                delivery.error_message = str(exc)
                broadcast.failure_count += 1
            await asyncio.sleep(1 / max(self.settings.broadcast_throttle_per_second, 1))

        broadcast.status = BroadcastStatus.COMPLETED if broadcast.failure_count == 0 else BroadcastStatus.FAILED
        broadcast.finished_at = utcnow()
        await track_event(self.session, broadcast.created_by_user_id, "broadcast_finished", {"broadcast_id": str(broadcast.id)})
        return broadcast
