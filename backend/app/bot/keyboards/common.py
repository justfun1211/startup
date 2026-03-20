from urllib.parse import urlparse

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.core.config import get_settings


def _supports_webapp(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    settings = get_settings()
    supports_webapp = _supports_webapp(settings.webapp_url)
    rows = [
        [KeyboardButton(text="Отправить идею")],
        [KeyboardButton(text="Купить запросы"), KeyboardButton(text="Пригласить друга")],
        [KeyboardButton(text="История")],
    ]
    if supports_webapp:
        rows.append([KeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=settings.webapp_url))])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


def report_ready_keyboard(report_id: str) -> InlineKeyboardMarkup:
    settings = get_settings()
    rows = []
    if _supports_webapp(settings.webapp_url):
        rows.append([InlineKeyboardButton(text="Открыть полный отчет", web_app=WebAppInfo(url=f"{settings.webapp_url}/reports/{report_id}"))])
    rows.append([InlineKeyboardButton(text="Новый анализ", callback_data="new_analysis")])
    rows.append([InlineKeyboardButton(text="Поделиться ботом", url=f"https://t.me/share/url?url=https://t.me/{settings.bot_username}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pricing_keyboard(packs) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"{pack.title} • {pack.stars_amount} XTR", callback_data=f"buy:{pack.code}")] for pack in packs]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
