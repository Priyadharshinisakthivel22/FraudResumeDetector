from app.services.scoring import ScoringService


def test_weight_constants_sum_to_100() -> None:
    total = (
        ScoringService.OTP_WEIGHT
        + ScoringService.PROFILE_WEIGHT
        + ScoringService.SKILL_WEIGHT
        + ScoringService.EXP_WEIGHT
    )
    assert total == 100.0
