import asyncio
import uuid

from aiogram.types import FSInputFile
from arq.connections import RedisSettings
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.keyboards.common import report_ready_keyboard
from app.core.config import get_settings
from app.core.constants import AnalysisStatus
from app.models.admin import AdminBroadcast
from app.models.analysis import AnalysisRun
from app.models.user import User
from app.services.ai.client import AIClient
from app.services.analysis_service import AnalysisService
from app.services.broadcasts.service import BroadcastService
from app.services.pdf.service import PdfService
from app.services.referrals.service import ReferralService
from app.utils.time import utcnow


settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
WorkerSession = async_sessionmaker(engine, expire_on_commit=False)
ai_semaphore = asyncio.Semaphore(settings.max_ai_concurrency)


async def process_analysis_run(ctx, analysis_id: str):
    async with WorkerSession() as session:
        analysis = await session.get(AnalysisRun, uuid.UUID(analysis_id))
        if analysis is None or analysis.status not in {AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING}:
            return
        analysis.status = AnalysisStatus.PROCESSING
        analysis.started_at = utcnow()
        bot = Bot(token=settings.bot_token)
        ai = AIClient()
        service = AnalysisService(session)
        pdf_service = PdfService()
        try:
            async with ai_semaphore:
                report, usage, latency_ms, model_name = await ai.analyze(analysis.input_text)
            pdf_path = await pdf_service.generate_report_pdf(str(analysis.id), analysis.input_text, report)
            await service.save_completed_report(analysis, report, model_name, usage, latency_ms, pdf_path)
            invitee = await session.get(User, analysis.user_id)
            await ReferralService(session).reward_inviter_for_first_success(invitee)
            await session.commit()
            await bot.send_message(
                chat_id=invitee.telegram_id,
                text=analysis.short_summary_text,
                reply_markup=report_ready_keyboard(str(analysis.id)),
            )
            if pdf_path:
                await bot.send_document(
                    chat_id=invitee.telegram_id,
                    document=FSInputFile(pdf_path),
                    caption="PDF-версия отчета готова.",
                )
        except Exception as exc:
            await service.mark_failed(analysis, exc.__class__.__name__, str(exc))
            await session.commit()
            invitee = await session.get(User, analysis.user_id)
            await bot.send_message(
                chat_id=invitee.telegram_id,
                text="Не удалось завершить анализ. Мы уже вернули запрос на баланс, попробуйте еще раз чуть позже.",
            )
        finally:
            await bot.session.close()


async def process_broadcast(ctx, broadcast_id: str):
    from app.main import get_bot

    async with WorkerSession() as session:
        broadcast = await session.get(AdminBroadcast, uuid.UUID(broadcast_id))
        if broadcast is None:
            return
        service = BroadcastService(session, get_bot())
        await service.run_broadcast(broadcast)
        await session.commit()


class WorkerSettings:
    functions = [process_analysis_run, process_broadcast]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
