from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.models.project_stakeholder import ProjectStakeholder
from app.schemas.stakeholders import StakeholderCreate, StakeholderOut
from app.services.audit import record_audit
from app.services.stakeholders import (
    ConsortiumShareExceededError,
    create_stakeholder,
    list_stakeholders,
)

router = APIRouter(prefix="/projects/{project_id}/stakeholders", tags=["stakeholders"])


@router.post("", response_model=StakeholderOut, status_code=status.HTTP_201_CREATED)
async def create_stakeholder_endpoint(
    project_id: UUID,
    payload: StakeholderCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> ProjectStakeholder:
    try:
        stakeholder = await create_stakeholder(session, project_id=project_id, payload=payload)
    except ConsortiumShareExceededError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="stakeholder.create",
        entity_type="project_stakeholder",
        entity_id=str(stakeholder.id),
        changes={
            "role": stakeholder.role.value,
            "organization_name": stakeholder.organization_name,
        },
    )
    await session.commit()
    return stakeholder


@router.get("", response_model=list[StakeholderOut])
async def list_stakeholders_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ProjectStakeholder]:
    return await list_stakeholders(session, project_id)
