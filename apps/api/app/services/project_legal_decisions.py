from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_legal_decision import ProjectLegalDecision


async def list_legal_decisions(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectLegalDecision]:
    result = await session.execute(
        select(ProjectLegalDecision)
        .where(ProjectLegalDecision.project_id == project_id)
        .order_by(
            ProjectLegalDecision.decision_date.nulls_last(),
            ProjectLegalDecision.decision_no,
        )
    )
    return list(result.scalars().all())
