from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.milestone import Milestone
from app.models.project import Project
from app.schemas.milestones import MilestoneCreate, MilestoneOut, MilestoneUpdate
from app.services.audit import record_audit
from app.services.milestones import (
    DuplicateMilestoneError,
    ScheduleRuleError,
    create_milestone,
    get_milestone,
    list_milestones,
    update_milestone,
)

MILESTONE_NOT_FOUND_DETAIL = "Không tìm thấy mốc tiến độ"

router = APIRouter(prefix="/projects/{project_id}/milestones", tags=["milestones"])


def _jsonable(values: dict[str, Any]) -> dict[str, str | None]:
    """Chuyển giá trị sang chuỗi để ghi vào nhật ký audit (date, Decimal, enum)."""
    return {key: None if value is None else str(value) for key, value in values.items()}


@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
async def create_milestone_endpoint(
    project_id: UUID,
    payload: MilestoneCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> MilestoneOut:
    try:
        milestone = await create_milestone(
            session, project_id=project_id, values=payload.model_dump()
        )
    except DuplicateMilestoneError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã mốc {exc} đã tồn tại trong dự án",
        ) from None
    except ScheduleRuleError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone.create",
        entity_type="milestone",
        entity_id=str(milestone.id),
        changes={"code": milestone.code, "baseline_end": str(milestone.baseline_end)},
    )
    output = MilestoneOut.from_milestone(milestone, date.today())
    await session.commit()
    return output


@router.get("", response_model=list[MilestoneOut])
async def list_milestones_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[MilestoneOut]:
    today = date.today()
    milestones = await list_milestones(session, project_id)
    return [MilestoneOut.from_milestone(milestone, today) for milestone in milestones]


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


@router.get("/{milestone_id}", response_model=MilestoneOut)
async def get_milestone_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> MilestoneOut:
    milestone = await _get_milestone_or_404(session, project_id, milestone_id)
    return MilestoneOut.from_milestone(milestone, date.today())


@router.patch("/{milestone_id}", response_model=MilestoneOut)
async def update_milestone_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    payload: MilestoneUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> MilestoneOut:
    milestone = await _get_milestone_or_404(session, project_id, milestone_id)
    changes = payload.model_dump(exclude_unset=True, exclude={"reason"})
    try:
        adjustment = await update_milestone(
            session,
            milestone,
            changes=changes,
            reason=payload.reason,
            actor_id=principal.user_id,
        )
    except ScheduleRuleError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone.update",
        entity_type="milestone",
        entity_id=str(milestone.id),
        changes=_jsonable(changes),
    )
    if adjustment is not None:
        await record_audit(
            session,
            actor_id=principal.user_id,
            action="milestone.adjust",
            entity_type="milestone",
            entity_id=str(milestone.id),
            changes={
                "previous_end": str(adjustment.previous_end),
                "new_end": str(adjustment.new_end),
                "reason": adjustment.reason,
            },
        )
    output = MilestoneOut.from_milestone(milestone, date.today())
    await session.commit()
    return output
