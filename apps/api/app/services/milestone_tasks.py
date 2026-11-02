from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.milestone_task import MilestoneTask


async def list_tasks_by_milestone(
    session: AsyncSession,
    milestone_ids: Sequence[UUID],
) -> dict[UUID, list[MilestoneTask]]:
    """Gom task theo mốc bằng một truy vấn, tránh gọi lặp theo từng mốc."""
    grouped: dict[UUID, list[MilestoneTask]] = {milestone_id: [] for milestone_id in milestone_ids}
    if not milestone_ids:
        return grouped
    result = await session.execute(
        select(MilestoneTask)
        .where(MilestoneTask.milestone_id.in_(milestone_ids))
        .order_by(MilestoneTask.sort_order, MilestoneTask.created_at)
    )
    for task in result.scalars().all():
        grouped[task.milestone_id].append(task)
    return grouped


async def get_task(
    session: AsyncSession,
    milestone_id: UUID,
    task_id: UUID,
) -> MilestoneTask | None:
    result = await session.execute(
        select(MilestoneTask).where(
            MilestoneTask.id == task_id,
            MilestoneTask.milestone_id == milestone_id,
        )
    )
    return result.scalar_one_or_none()


async def create_task(
    session: AsyncSession,
    *,
    milestone_id: UUID,
    values: Mapping[str, Any],
) -> MilestoneTask:
    task = MilestoneTask(milestone_id=milestone_id, **values)
    session.add(task)
    await session.flush()
    return task


async def update_task(
    session: AsyncSession,
    task: MilestoneTask,
    *,
    changes: Mapping[str, Any],
) -> MilestoneTask:
    for field, value in changes.items():
        setattr(task, field, value)
    await session.flush()
    return task


async def delete_task(session: AsyncSession, task: MilestoneTask) -> None:
    await session.delete(task)
    await session.flush()
