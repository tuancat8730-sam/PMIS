import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_hcm_project
from app.models.audit_log import AuditLog
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.project import Project

pytestmark = pytest.mark.integration

HCM_UNIT_COUNT = 8


async def test_seed_creates_hcm_project_and_eight_units_once(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    inserted = await seed_hcm_project(session_factory)

    # Assert
    assert inserted == HCM_UNIT_COUNT
    async with session_factory() as session:
        project_count = await session.scalar(select(func.count()).select_from(Project))
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
    assert project_count == 1
    assert unit_count == HCM_UNIT_COUNT


async def test_running_seed_twice_does_not_duplicate_records(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_hcm_project(session_factory)

    # Act
    second_run_inserted = await seed_hcm_project(session_factory)

    # Assert
    assert second_run_inserted == 0
    async with session_factory() as session:
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
        seed_audit_count = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == "beneficiary_unit.seed")
        )
    assert unit_count == HCM_UNIT_COUNT
    assert seed_audit_count == HCM_UNIT_COUNT


async def test_seed_writes_audit_without_actor(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        actors = (
            (
                await session.execute(
                    select(AuditLog.actor_id).where(AuditLog.action == "project.seed")
                )
            )
            .scalars()
            .all()
        )
    assert actors == [None]
