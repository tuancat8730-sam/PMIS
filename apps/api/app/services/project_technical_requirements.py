from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_technical_requirement import ProjectTechnicalRequirement


async def list_technical_requirements(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectTechnicalRequirement]:
    result = await session.execute(
        select(ProjectTechnicalRequirement)
        .where(ProjectTechnicalRequirement.project_id == project_id)
        .order_by(ProjectTechnicalRequirement.sort_order, ProjectTechnicalRequirement.item)
    )
    return list(result.scalars().all())
