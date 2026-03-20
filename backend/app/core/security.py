import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime, timezone

from fastapi import Header, HTTPException, status
from itsdangerous import URLSafeSerializer
from pydantic import BaseModel

from app.core.config import get_settings


class SessionPrincipal(BaseModel):
    telegram_id: int


def build_session_serializer() -> URLSafeSerializer:
    settings = get_settings()
    return URLSafeSerializer(settings.webhook_secret_token, salt="proofbot-session")


def issue_session_token(telegram_id: int) -> str:
    serializer = build_session_serializer()
    return serializer.dumps({"telegram_id": telegram_id})


def decode_session_token(token: str) -> SessionPrincipal:
    serializer = build_session_serializer()
    try:
        data = serializer.loads(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительная сессия") from exc
    return SessionPrincipal(telegram_id=int(data["telegram_id"]))


async def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    return authorization.removeprefix("Bearer ").strip()


def validate_telegram_init_data(init_data_raw: str) -> dict:
    settings = get_settings()
    pairs = urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True)
    payload = dict(pairs)
    provided_hash = payload.pop("hash", None)
    if not provided_hash:
        raise HTTPException(status_code=400, detail="Отсутствует hash в initData")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, provided_hash):
        raise HTTPException(status_code=401, detail="Неверная подпись Telegram initData")

    auth_date = int(payload.get("auth_date", "0"))
    now = int(datetime.now(timezone.utc).timestamp())
    if now - auth_date > settings.telegram_login_max_age_seconds:
        raise HTTPException(status_code=401, detail="Сессия Telegram устарела")

    user_raw = payload.get("user")
    if not user_raw:
        raise HTTPException(status_code=400, detail="Отсутствует Telegram user")
    return json.loads(user_raw)
