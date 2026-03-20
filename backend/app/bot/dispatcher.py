from aiogram import Dispatcher

from app.bot.handlers.common import router as common_router


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(common_router)
    return dispatcher
