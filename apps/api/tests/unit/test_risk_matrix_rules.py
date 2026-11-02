import pytest

from app.core.risk_matrix_rules import risk_score
from app.models.risk_issue import RiskLevel


@pytest.mark.unit
def test_score_is_product_of_impact_and_likelihood_ranks() -> None:
    # Arrange
    impact = RiskLevel.VERY_HIGH
    likelihood = RiskLevel.HIGH

    # Act
    score = risk_score(impact, likelihood)

    # Assert
    assert score == 12


@pytest.mark.unit
def test_score_is_none_when_either_level_is_missing() -> None:
    # Arrange / Act / Assert
    assert risk_score(None, RiskLevel.HIGH) is None
    assert risk_score(RiskLevel.LOW, None) is None
