from pydantic import BaseModel


class ReferralMeSchema(BaseModel):
    referral_link: str
    referral_code: str
    invited_count: int
    rewarded_count: int
    total_bonus_requests: int
    invitee_bonus_requests: int
    inviter_bonus_requests: int

