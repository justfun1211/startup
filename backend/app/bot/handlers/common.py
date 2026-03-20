from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import main_menu_keyboard, pricing_keyboard
from app.core.config import get_settings
from app.core.queue import get_arq_pool
from app.db.session import SessionLocal
from app.schemas.analysis import AnalysisCreateSchema
from app.services.analysis_service import AnalysisService
from app.services.credits.service import CreditsService
from app.services.payments.service import PaymentsService
from app.services.referrals.service import ReferralService
from app.services.users import UserService
from app.utils.referrals import parse_referral_payload


router = Router()


async def _load_user(message: Message) -> tuple[AsyncSession, object]:
    session = SessionLocal()
    user_service = UserService(session)
    user, _ = await user_service.get_or_create_telegram_user(message.from_user.model_dump())
    return session, user


def _is_https_webapp() -> bool:
    return urlparse(get_settings().webapp_url).scheme == "https"


@router.message(Command("start"))
async def start_handler(message: Message, command: CommandObject) -> None:
    session, user = await _load_user(message)
    try:
        referral_code = parse_referral_payload(command.args)
        if referral_code:
            await ReferralService(session).attach_referrer(user, referral_code)

        balance = await CreditsService(session).get_or_create_balance(user.id)
        await session.commit()

        extra_hint = ""
        if not _is_https_webapp():
            extra_hint = "\n\nMini App кнопка скрыта локально: Telegram принимает Web App только по HTTPS."

        await message.answer(
            "Бот анализирует стартап-идеи и превращает их в структурированный план запуска.\n\n"
            f"Сейчас у вас доступно {balance.available_requests} запросов.{extra_hint}",
            reply_markup=main_menu_keyboard(),
        )
    finally:
        await session.close()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "/start — начать работу\n"
        "/history — последние отчеты\n"
        "/buy — купить запросы\n"
        "/ref — пригласить друга\n"
        "/paysupport — помощь по оплате\n"
        "/admin — вход в админку"
    )


@router.message(Command("paysupport"))
async def paysupport_handler(message: Message) -> None:
    await message.answer(get_settings().pay_support_text)


@router.message(Command("buy"))
@router.message(F.text == "Купить запросы")
async def buy_handler(message: Message) -> None:
    session, _user = await _load_user(message)
    try:
        packs = await PaymentsService(session).list_packs()
        await session.commit()
        await message.answer("Выберите пакет запросов:", reply_markup=pricing_keyboard(packs))
    finally:
        await session.close()


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback_handler(callback: CallbackQuery) -> None:
    session, user = await _load_user(callback.message)
    try:
        pack_code = callback.data.split(":", 1)[1]
        intent = await PaymentsService(session).create_payment_intent(user, pack_code)
        await session.commit()
        await callback.message.answer_invoice(
            title=intent.pack.title,
            description=intent.pack.description,
            payload=intent.payment.invoice_payload,
            currency="XTR",
            prices=[LabeledPrice(label=intent.pack.title, amount=intent.pack.stars_amount)],
            provider_token=get_settings().stars_provider_token,
            start_parameter=f"pack_{intent.pack.code}",
        )
        await callback.answer()
    finally:
        await session.close()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    async with SessionLocal() as session:
        service = PaymentsService(session)
        try:
            await service.mark_pre_checkout(query.invoice_payload, query.model_dump())
            await session.commit()
            await query.answer(ok=True)
        except Exception:
            await session.rollback()
            await query.answer(ok=False, error_message="Не удалось подтвердить оплату. Попробуйте еще раз.")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    payment = message.successful_payment
    async with SessionLocal() as session:
        service = PaymentsService(session)
        await service.mark_paid_once(
            payment.invoice_payload,
            payment.telegram_payment_charge_id,
            payment.provider_payment_charge_id,
            message.model_dump(mode="json"),
        )
        await session.commit()
    await message.answer("Оплата прошла успешно. Запросы уже начислены на ваш баланс.")


@router.message(Command("ref"))
@router.message(F.text == "Пригласить друга")
async def referral_handler(message: Message) -> None:
    session, user = await _load_user(message)
    try:
        stats = await ReferralService(session).stats_for_user(user)
        await session.commit()
        await message.answer(
            f"Ваша ссылка:\nhttps://t.me/{get_settings().bot_username}?start=ref_{user.referral_code}\n\n"
            f"Приглашено: {stats['invited_count']}\n"
            f"Наград получено: {stats['rewarded_count']}\n"
            f"Бонус за приглашенного: {stats['inviter_bonus_requests']} запрос(а)\n"
            f"Бонус новичку: {stats['invitee_bonus_requests']} запрос(а)"
        )
    finally:
        await session.close()


@router.message(Command("history"))
@router.message(F.text == "История")
async def history_handler(message: Message) -> None:
    session, user = await _load_user(message)
    try:
        items = await AnalysisService(session).list_reports(user.id)
        await session.commit()
        if not items:
            text = "История пока пустая. Отправьте идею, и мы соберем первый отчет."
        else:
            text = "Последние отчеты:\n\n" + "\n\n──────────\n\n".join(
                f"{item.created_at:%d.%m %H:%M} • {item.status}\n\n{item.short_summary_text or 'Отчет еще готовится'}"
                for item in items[:5]
            )
        await message.answer(text)
    finally:
        await session.close()


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    session, user = await _load_user(message)
    try:
        await session.commit()
        if not user.is_admin:
            await message.answer("Эта команда доступна только администраторам.")
        else:
            await message.answer(f"Админка доступна в Mini App:\n{get_settings().webapp_url}/admin")
    finally:
        await session.close()


@router.message(F.text == "Отправить идею")
async def idea_hint_handler(message: Message) -> None:
    await message.answer(
        "Отправьте одним сообщением описание стартап-идеи. Чем конкретнее контекст, тем полезнее будет анализ."
    )


@router.message(F.text)
async def idea_handler(message: Message) -> None:
    text = (message.text or "").strip()
    if text.startswith("/"):
        return
    if text in {"Купить запросы", "Пригласить друга", "История", "Отправить идею", "Открыть Mini App"}:
        return

    session, user = await _load_user(message)
    try:
        balance = await CreditsService(session).get_or_create_balance(user.id)
        if balance.available_requests < 1:
            await message.answer("Бесплатные запросы закончились. Откройте /buy и пополните баланс.")
            return

        try:
            payload = AnalysisCreateSchema(source="bot", input_text=text)
        except ValidationError:
            await message.answer(
                "Опишите идею чуть подробнее. Нужно хотя бы 10 символов, чтобы анализ получился полезным."
            )
            return

        await AnalysisService(session).enqueue_analysis(
            user,
            payload,
            await get_arq_pool(),
        )
        await session.commit()
        await message.answer("Идея принята в работу. Когда отчет будет готов, пришлем его сюда.")
    except ValueError as exc:
        await session.rollback()
        await message.answer(str(exc))
    finally:
        await session.close()
