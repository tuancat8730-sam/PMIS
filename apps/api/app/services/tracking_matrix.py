from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.milestone import Milestone
from app.models.risk_issue import RiskIssue


async def list_schedule_rows(session: AsyncSession, project_id: UUID) -> list[Milestone]:
    result = await session.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.baseline_end, Milestone.code)
    )
    return list(result.scalars().all())


async def list_risk_rows(session: AsyncSession, project_id: UUID) -> list[RiskIssue]:
    result = await session.execute(
        select(RiskIssue).where(RiskIssue.project_id == project_id).order_by(RiskIssue.code)
    )
    return list(result.scalars().all())
