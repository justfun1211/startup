import asyncio
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from structlog import get_logger

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.twa import router as twa_router
from app.bot.dispatcher import build_dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)
bot_instance = Bot(token=settings.bot_token) if settings.bot_token else None
dispatcher = build_dispatcher()
polling_task: asyncio.Task | None = None


def get_bot() -> Bot:
    if bot_instance is None:
        raise RuntimeError("BOT_TOKEN не задан")
    return bot_instance


@asynccontextmanager
async def lifespan(_: FastAPI):
    global polling_task
    logger.info("app_lifespan_started", bot_mode=settings.bot_mode, has_token=bool(settings.bot_token))
    
    try:
        if bot_instance and settings.bot_mode == "polling":
            logger.info("bot_polling_starting")
            await bot_instance.delete_webhook(drop_pending_updates=False)
            logger.info("bot_webhook_deleted_for_polling")
            polling_task = asyncio.create_task(dispatcher.start_polling(bot_instance, handle_signals=False))
            logger.info("bot_polling_started_task")
        elif bot_instance and settings.bot_mode == "webhook" and settings.webhook_base_url:
            logger.info("bot_webhook_setting", url=settings.webhook_base_url)
            await bot_instance.set_webhook(
                url=f"{settings.webhook_base_url}/webhook/telegram",
                secret_token=settings.webhook_secret_token,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
            logger.info("bot_webhook_set")
        else:
            logger.warning("bot_not_started_check_env", mode=settings.bot_mode, has_token=bool(settings.bot_token))
    except Exception as e:
        logger.error("bot_startup_failed", error=str(e), exc_info=True)

    yield
    if polling_task:
        polling_task.cancel()
    if bot_instance:
        if settings.bot_mode == "webhook":
            await bot_instance.delete_webhook(drop_pending_updates=False)
        await bot_instance.session.close()


app = FastAPI(title="Proofbot API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(twa_router)
app.include_router(me_router)
app.include_router(admin_router)


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    if settings.webhook_secret_token and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret_token:
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    update = Update.model_validate(await request.json())
    await dispatcher.feed_update(get_bot(), update)
    return {"ok": True}
