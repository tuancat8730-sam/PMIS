from app.models.risk_issue import RiskLevel

RISK_LEVEL_RANK: dict[RiskLevel, int] = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.VERY_HIGH: 4,
}


def risk_score(impact: RiskLevel | None, likelihood: RiskLevel | None) -> int | None:
    """Điểm = thứ hạng tác động × thứ hạng khả năng (1–16).

    Thiếu một trong hai mức thì không chấm điểm.
    """
    if impact is None or likelihood is None:
        return None
    return RISK_LEVEL_RANK[impact] * RISK_LEVEL_RANK[likelihood]
