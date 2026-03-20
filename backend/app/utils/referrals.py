def parse_referral_payload(payload: str | None) -> str | None:
    if not payload:
        return None
    normalized = payload.strip()
    if normalized.startswith("ref_") and len(normalized) > 4:
        return normalized[4:]
    return None

