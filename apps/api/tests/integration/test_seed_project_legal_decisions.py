from decimal import Decimal

import pytest
from fastapi import FastAPI
from sqlalchemy import select

from app.db.seed_real_projects import seed_hcm_project, seed_lam_dong_project
from app.models.project import Project
from app.models.project_legal_decision import LegalDecisionKind, ProjectLegalDecision

pytestmark = pytest.mark.integration

HCM_DECISION_COUNT = 4
LAM_DONG_DECISION_COUNT = 2
HCM_CODE = "SGD-HCM-CSVC-2026"
LAM_DONG_CODE = "SGD-LD-TB10-2026"


async def test_seed_hcm_legal_decisions_with_investment_amount_and_idempotent(
    app: FastAPI,
) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        project_id = (
            await session.execute(select(Project.id).where(Project.code == HCM_CODE))
        ).scalar_one()
        decisions = (
            (
                await session.execute(
                    select(ProjectLegalDecision).where(
                        ProjectLegalDecision.project_id == project_id
                    )
                )
            )
            .scalars()
            .all()
        )
    by_no = {decision.decision_no: decision for decision in decisions}
    assert len(decisions) == HCM_DECISION_COUNT
    assert by_no["1595/QĐ-SGDĐT"].kind == LegalDecisionKind.PROJECT_APPROVAL
    assert by_no["1595/QĐ-SGDĐT"].amount == Decimal("5999498939.00")
    assert by_no["1595/QĐ-SGDĐT"].execution_period is not None


async def test_seed_lam_dong_legal_decisions_keeps_unknown_fields_empty(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_lam_dong_project(session_factory)

    # Assert
    async with session_factory() as session:
        project_id = (
            await session.execute(select(Project.id).where(Project.code == LAM_DONG_CODE))
        ).scalar_one()
        decisions = (
            (
                await session.execute(
                    select(ProjectLegalDecision).where(
                        ProjectLegalDecision.project_id == project_id
                    )
                )
            )
            .scalars()
            .all()
        )
    # Số QĐ phê duyệt TMĐT chính thức (QĐ 2891) chưa đọc: không có dòng PROJECT_APPROVAL.
    assert len(decisions) == LAM_DONG_DECISION_COUNT
    assert all(decision.kind != LegalDecisionKind.PROJECT_APPROVAL for decision in decisions)
    assert all(decision.funding_source is None for decision in decisions)
