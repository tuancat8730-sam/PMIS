from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import SessionDep, WriteRateLimitDep, project_role_guard
from app.api.v1.milestones import MILESTONE_NOT_FOUND_DETAIL
from app.core.rbac import Principal, Role, get_current_principal
from app.models.milestone import Milestone
from app.models.project import Project
from app.schemas.milestone_children import TaskCreate, TaskOut, TaskUpdate
from app.services.audit import record_audit
from app.services.milestone_tasks import create_task, delete_task, get_task, update_task
from app.services.milestones import get_milestone

TASK_NOT_FOUND_DETAIL = "Không tìm thấy task con"
TASK_WRITE_ROLES = (Role.PM, Role.SUPERVISION_CONSULTANT)

router = APIRouter(
    prefix="/projects/{project_id}/milestones/{milestone_id}/tasks",
    tags=["milestone-tasks"],
)

ProjectGuardDep = Annotated[Project, Depends(project_role_guard(*TASK_WRITE_ROLES))]
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]


async def _get_milestone_or_404(
    session: SessionDep,
    project_id: UUID,
    milestone_id: UUID,
) -> Milestone:
    milestone = await get_milestone(session, project_id, milestone_id)
    if milestone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MILESTONE_NOT_FOUND_DETAIL
        )
    return milestone


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    payload: TaskCreate,
    _project: ProjectGuardDep,
    principal: PrincipalDep,
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> TaskOut:
    milestone = await _get_milestone_or_404(session, project_id, milestone_id)
    task = await create_task(session, milestone_id=milestone.id, values=payload.model_dump())

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone_task.create",
        entity_type="milestone_task",
        entity_id=str(task.id),
        changes={"milestone_id": str(milestone.id), "name": task.name},
    )
    output = TaskOut.from_task(task, date.today())
    await session.commit()
    return output


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    task_id: UUID,
    payload: TaskUpdate,
    _project: ProjectGuardDep,
    principal: PrincipalDep,
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> TaskOut:
    milestone = await _get_milestone_or_404(session, project_id, milestone_id)
    task = await get_task(session, milestone.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND_DETAIL)
    changes = payload.model_dump(exclude_unset=True)
    task = await update_task(session, task, changes=changes)

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone_task.update",
        entity_type="milestone_task",
        entity_id=str(task.id),
        changes={"fields": ", ".join(sorted(changes))},
    )
    output = TaskOut.from_task(task, date.today())
    await session.commit()
    return output


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    task_id: UUID,
    _project: ProjectGuardDep,
    principal: PrincipalDep,
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> Response:
    milestone = await _get_milestone_or_404(session, project_id, milestone_id)
    task = await get_task(session, milestone.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND_DETAIL)
    deleted_id = str(task.id)
    await delete_task(session, task)

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone_task.delete",
        entity_type="milestone_task",
        entity_id=deleted_id,
        changes={"milestone_id": str(milestone.id)},
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
