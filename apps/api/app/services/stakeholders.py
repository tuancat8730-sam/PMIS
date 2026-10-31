from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_stakeholder import ProjectStakeholder, StakeholderRole
from app.schemas.stakeholders import StakeholderCreate

MAX_CONSORTIUM_SHARE = Decimal("100")


class ConsortiumShareExceededError(Exception):
    """Tổng tỷ lệ liên danh của dự án vượt 100%."""


def check_consortium_share_total(existing_shares: Sequence[Decimal], new_share: Decimal) -> None:
    total = sum(existing_shares, Decimal("0")) + new_share
    if total > MAX_CONSORTIUM_SHARE:
        raise ConsortiumShareExceededError(f"Tổng tỷ lệ liên danh là {total}%, tối đa 100%")


async def _lock_project(session: AsyncSession, project_id: UUID) -> None:
    # Khóa dòng dự án để hai lần thêm liên danh đồng thời không cùng vượt 100%.
    await session.execute(select(Project.id).where(Project.id == project_id).with_for_update())


async def _consortium_shares(session: AsyncSession, project_id: UUID) -> list[Decimal]:
    result = await session.execute(
        select(ProjectStakeholder.share_percentage).where(
            ProjectStakeholder.project_id == project_id,
            ProjectStakeholder.role == StakeholderRole.CONSORTIUM_MEMBER,
            ProjectStakeholder.share_percentage.is_not(None),
        )
    )
    return [share for share in result.scalars().all() if share is not None]


async def create_stakeholder(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: StakeholderCreate,
) -> ProjectStakeholder:
    if payload.role == StakeholderRole.CONSORTIUM_MEMBER and payload.share_percentage is not None:
        await _lock_project(session, project_id)
        check_consortium_share_total(
            await _consortium_shares(session, project_id),
            payload.share_percentage,
        )
    stakeholder = ProjectStakeholder(project_id=project_id, **payload.model_dump())
    session.add(stakeholder)
    await session.flush()
    return stakeholder


async def list_stakeholders(session: AsyncSession, project_id: UUID) -> list[ProjectStakeholder]:
    result = await session.execute(
        select(ProjectStakeholder)
        .where(ProjectStakeholder.project_id == project_id)
        .order_by(ProjectStakeholder.organization_name)
    )
    return list(result.scalars().all())
