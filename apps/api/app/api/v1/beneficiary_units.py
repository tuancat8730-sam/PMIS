from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.beneficiary_unit import CLUSTER_CODE_MAX_LENGTH, BeneficiaryUnit, UnitType
from app.models.project import Project
from app.schemas.beneficiary_units import (
    BeneficiaryUnitCreate,
    BeneficiaryUnitOut,
    BeneficiaryUnitUpdate,
)
from app.services.audit import record_audit
from app.services.beneficiary_units import (
    DuplicateUnitError,
    apply_update,
    create_unit,
    get_unit,
    list_units,
)

UNIT_NOT_FOUND_DETAIL = "Không tìm thấy đơn vị thụ hưởng"

router = APIRouter(prefix="/projects/{project_id}/beneficiary-units", tags=["beneficiary-units"])


@router.post("", response_model=BeneficiaryUnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit_endpoint(
    project_id: UUID,
    payload: BeneficiaryUnitCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> BeneficiaryUnit:
    try:
        unit = await create_unit(session, project_id=project_id, values=payload.model_dump())
    except DuplicateUnitError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã đơn vị {exc} đã tồn tại trong dự án",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="beneficiary_unit.create",
        entity_type="beneficiary_unit",
        entity_id=str(unit.id),
        changes={"unit_code": unit.unit_code, "official_name": unit.official_name},
    )
    await session.commit()
    return unit


@router.get("", response_model=list[BeneficiaryUnitOut])
async def list_units_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
    cluster_code: Annotated[
        str | None, Query(min_length=1, max_length=CLUSTER_CODE_MAX_LENGTH)
    ] = None,
    unit_type: UnitType | None = None,
) -> list[BeneficiaryUnit]:
    return await list_units(
        session,
        project_id,
        cluster_code=cluster_code,
        unit_type=unit_type,
    )


@router.get("/{unit_id}", response_model=BeneficiaryUnitOut)
async def get_unit_endpoint(
    project_id: UUID,
    unit_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> BeneficiaryUnit:
    unit = await get_unit(session, project_id, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=UNIT_NOT_FOUND_DETAIL)
    return unit


@router.patch("/{unit_id}", response_model=BeneficiaryUnitOut)
async def update_unit_endpoint(
    project_id: UUID,
    unit_id: UUID,
    payload: BeneficiaryUnitUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> BeneficiaryUnit:
    unit = await get_unit(session, project_id, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=UNIT_NOT_FOUND_DETAIL)

    changes = apply_update(unit, payload.model_dump(exclude_unset=True))
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="beneficiary_unit.update",
        entity_type="beneficiary_unit",
        entity_id=str(unit.id),
        changes=changes,
    )
    await session.commit()
    return unit
