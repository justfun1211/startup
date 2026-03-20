import secrets
import uuid


def generate_referral_code() -> str:
    return secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:10].upper()


def generate_invoice_payload(user_id: uuid.UUID, pack_code: str) -> str:
    return f"stars:{pack_code}:{user_id}:{secrets.token_hex(6)}"

