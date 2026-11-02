from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_budget_item import ProjectBudgetItem


async def list_budget_items(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectBudgetItem]:
    result = await session.execute(
        select(ProjectBudgetItem)
        .where(ProjectBudgetItem.project_id == project_id)
        .order_by(ProjectBudgetItem.sort_order, ProjectBudgetItem.category)
    )
    return list(result.scalars().all())
