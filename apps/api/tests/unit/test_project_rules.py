from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.projects import ProjectCreate
from app.schemas.stakeholders import StakeholderCreate
from app.services.stakeholders import ConsortiumShareExceededError, check_consortium_share_total

pytestmark = pytest.mark.unit

PROJECT_FIELDS = {
    "name": "Dự án thử nghiệm",
    "short_name": "Thử nghiệm",
    "archetype": "IT_SYSTEM",
    "investor_name": "Sở GD&ĐT TP.HCM",
    "total_investment": "1000000.00",
}


def test_consortium_shares_totalling_exactly_100_are_accepted() -> None:
    # Arrange
    existing = [Decimal("95.00")]

    # Act / Assert
    check_consortium_share_total(existing, Decimal("5.00"))


def test_consortium_shares_over_100_are_rejected() -> None:
    # Arrange
    existing = [Decimal("95.00"), Decimal("5.00")]

    # Act / Assert
    with pytest.raises(ConsortiumShareExceededError):
        check_consortium_share_total(existing, Decimal("0.01"))


def test_consortium_check_accepts_first_member_at_100_percent() -> None:
    # Arrange
    existing: list[Decimal] = []

    # Act / Assert
    check_consortium_share_total(existing, Decimal("100.00"))


def test_share_above_100_percent_fails_validation() -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        StakeholderCreate(
            role="CONSORTIUM_MEMBER",
            organization_name="DTH",
            share_percentage=Decimal("100.01"),
        )


def test_negative_share_fails_validation() -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        StakeholderCreate(
            role="CONSORTIUM_MEMBER",
            organization_name="DTH",
            share_percentage=Decimal("-1"),
        )


@pytest.mark.parametrize("code", ["sgd-hcm-2026", "AB", "SGD HCM"])
def test_project_code_outside_pattern_fails_validation(code: str) -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        ProjectCreate(code=code, **PROJECT_FIELDS)


def test_project_code_in_upper_snake_pattern_passes_validation() -> None:
    # Act
    project = ProjectCreate(code="SGD-LD-TB10-2026", **PROJECT_FIELDS)

    # Assert
    assert project.code == "SGD-LD-TB10-2026"


def test_end_date_equal_to_start_date_is_accepted() -> None:
    # Act
    project = ProjectCreate(
        code="SGD-HCM-2026",
        start_date="2026-01-15",
        end_date="2026-01-15",
        **PROJECT_FIELDS,
    )

    # Assert
    assert project.start_date == project.end_date
