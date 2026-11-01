from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.delivery_matrix import DeliveryMatrixError, DeliveryTransitionError
from app.core.rbac import Principal, Role, get_current_principal
from app.models.delivery_handover import DeliveryHandover
from app.models.project import Project
from app.schemas.equipment import (
    DeliveryHandoverOut,
    DeliveryStatusUpdate,
    HandoverGenerateOut,
)
from app.services.audit import record_audit
from app.services.delivery_handovers import (
    generate_handovers,
    get_handover,
    list_handovers,
    update_handover_status,
)

HANDOVER_NOT_FOUND_DETAIL = "Không tìm thấy dòng giao hàng"
CLUSTER_CODE_QUERY_MAX_LENGTH = 50
FIELD_STATUS_ROLES = (Role.PM, Role.SUPERVISION_CONSULTANT, Role.FIELD_ENGINEER)

router = APIRouter(prefix="/projects/{project_id}/delivery-handovers", tags=["delivery"])


def _to_out(handover: DeliveryHandover, cluster_code: str) -> DeliveryHandoverOut:
    return DeliveryHandoverOut(
        id=handover.id,
        beneficiary_unit_id=handover.beneficiary_unit_id,
        cluster_code=cluster_code,
        batch_code=handover.batch_code,
        planned_date=handover.planned_date,
        actual_date=handover.actual_date,
        delivery_status=handover.delivery_status,
    )


@router.get("", response_model=list[DeliveryHandoverOut])
async def list_handovers_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
    cluster_code: Annotated[
        str | None, Query(min_length=1, max_length=CLUSTER_CODE_QUERY_MAX_LENGTH)
    ] = None,
    batch_code: Literal["DOT_1", "DOT_2", "DOT_3", "TONG_THE"] | None = None,
) -> list[DeliveryHandoverOut]:
    rows = await list_handovers(
        session,
        project_id=project_id,
        cluster_code=cluster_code,
        batch_code=batch_code,
    )
    return [_to_out(handover, cluster) for handover, cluster in rows]


@router.post(
    "/generate",
    response_model=HandoverGenerateOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_handovers_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> HandoverGenerateOut:
    try:
        created = await generate_handovers(session, project_id=project_id)
    except DeliveryMatrixError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="delivery_handover.generate",
        entity_type="delivery_handover",
        entity_id=str(project_id),
        changes={"created": created},
    )
    output = HandoverGenerateOut(created=created)
    await session.commit()
    return output


@router.patch("/{handover_id}/status", response_model=DeliveryHandoverOut)
async def update_handover_status_endpoint(
    project_id: UUID,
    handover_id: UUID,
    payload: DeliveryStatusUpdate,
    _project: Annotated[Project, Depends(project_role_guard(*FIELD_STATUS_ROLES))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> DeliveryHandoverOut:
    row = await get_handover(session, project_id=project_id, handover_id=handover_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=HANDOVER_NOT_FOUND_DETAIL,
        )
    handover, cluster_code = row
    previous_status = handover.delivery_status
    try:
        update_handover_status(handover, payload.delivery_status)
    except DeliveryTransitionError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="delivery_handover.status",
        entity_type="delivery_handover",
        entity_id=str(handover.id),
        changes={"from": previous_status, "to": handover.delivery_status},
    )
    output = _to_out(handover, cluster_code)
    await session.commit()
    return output
