from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    ANY_PROJECT_ROLE,
    SessionDep,
    WriteRateLimitDep,
    ensure_project_role,
    project_role_guard,
)
from app.core.rbac import Principal, Role, get_current_principal
from app.models.hold_point import ConfirmingParty, HoldPoint
from app.models.project import Project
from app.schemas.hold_points import ConfirmationCreate, HoldPointCreate, HoldPointOut
from app.services.audit import record_audit
from app.services.hold_points import (
    DuplicateConfirmationError,
    DuplicateHoldPointError,
    add_confirmation,
    confirmed_parties_by_hold_point,
    create_hold_point,
    get_hold_point,
    list_hold_points,
)
from app.services.milestones import get_milestone

HOLD_POINT_NOT_FOUND_DETAIL = "Không tìm thấy điểm dừng"
MILESTONE_NOT_IN_PROJECT_DETAIL = "Mốc không thuộc dự án này"

# Mỗi bên chỉ được xác nhận bằng đúng vai trò của bên đó trong dự án.
PARTY_REQUIRED_ROLE: dict[ConfirmingParty, Role] = {
    ConfirmingParty.CDT: Role.PM,
    ConfirmingParty.TVGS: Role.SUPERVISION_CONSULTANT,
    ConfirmingParty.NHA_THAU: Role.CONTRACTOR,
}

router = APIRouter(prefix="/projects/{project_id}/hold-points", tags=["hold-points"])


@router.post("", response_model=HoldPointOut, status_code=status.HTTP_201_CREATED)
async def create_hold_point_endpoint(
    project_id: UUID,
    payload: HoldPointCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> HoldPointOut:
    if payload.milestone_id is not None:
        milestone = await get_milestone(session, project_id, payload.milestone_id)
        if milestone is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=MILESTONE_NOT_IN_PROJECT_DETAIL,
            )
    try:
        hold_point = await create_hold_point(
            session,
            project_id=project_id,
            code=payload.code,
            name=payload.name,
            milestone_id=payload.milestone_id,
        )
    except DuplicateHoldPointError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã điểm dừng {exc} đã tồn tại trong dự án",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="hold_point.create",
        entity_type="hold_point",
        entity_id=str(hold_point.id),
        changes={"code": hold_point.code},
    )
    output = HoldPointOut.from_hold_point(hold_point, set())
    await session.commit()
    return output


@router.get("", response_model=list[HoldPointOut])
async def list_hold_points_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[HoldPointOut]:
    hold_points = await list_hold_points(session, project_id)
    confirmed = await confirmed_parties_by_hold_point(session, [hp.id for hp in hold_points])
    return [HoldPointOut.from_hold_point(hp, confirmed[hp.id]) for hp in hold_points]


@router.post(
    "/{hold_point_id}/confirmations",
    response_model=HoldPointOut,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_hold_point_endpoint(
    project_id: UUID,
    hold_point_id: UUID,
    payload: ConfirmationCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> HoldPointOut:
    hold_point = await _get_hold_point_or_404(session, project_id, hold_point_id)
    await ensure_project_role(
        session,
        principal,
        project_id,
        (PARTY_REQUIRED_ROLE[payload.party],),
    )
    try:
        await add_confirmation(
            session,
            hold_point=hold_point,
            party=payload.party,
            evidence_ref=payload.evidence_ref,
            confirmed_by=principal.user_id,
        )
    except DuplicateConfirmationError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bên {exc} đã xác nhận điểm dừng này",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="hold_point.confirm",
        entity_type="hold_point",
        entity_id=str(hold_point.id),
        changes={"party": payload.party.value},
    )
    confirmed = await confirmed_parties_by_hold_point(session, [hold_point.id])
    output = HoldPointOut.from_hold_point(hold_point, confirmed[hold_point.id])
    await session.commit()
    return output


async def _get_hold_point_or_404(
    session: SessionDep,
    project_id: UUID,
    hold_point_id: UUID,
) -> HoldPoint:
    hold_point = await get_hold_point(session, project_id, hold_point_id)
    if hold_point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=HOLD_POINT_NOT_FOUND_DETAIL
        )
    return hold_point
