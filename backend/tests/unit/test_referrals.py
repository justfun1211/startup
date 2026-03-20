from app.utils.referrals import parse_referral_payload


def test_referral_code_parsing():
    assert parse_referral_payload("ref_ABC123") == "ABC123"
    assert parse_referral_payload("bad") is None

