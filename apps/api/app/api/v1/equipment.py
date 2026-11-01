from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.core.sample_criteria import SampleInspectionError
from app.models.equipment import EquipmentCatalog, SampleInspection
from app.models.project import Project
from app.schemas.equipment import (
    EquipmentCatalogCreate,
    EquipmentCatalogOut,
    SampleInspectionCreate,
    SampleInspectionOut,
)
from app.services.audit import record_audit
from app.services.equipment import (
    DuplicateCatalogItemError,
    create_catalog_item,
    create_sample_inspection,
    get_catalog_item,
    list_catalog,
    list_sample_inspections,
)

CATALOG_ITEM_NOT_FOUND_DETAIL = "Không tìm thấy mã hàng"
DUPLICATE_CATALOG_ITEM_DETAIL = "Mã hàng đã có trong đợt này của dự án"

router = APIRouter(prefix="/projects/{project_id}/equipment", tags=["equipment"])


@router.get("/catalog", response_model=list[EquipmentCatalogOut])
async def list_catalog_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[EquipmentCatalog]:
    return await list_catalog(session, project_id)


@router.post(
    "/catalog",
    response_model=EquipmentCatalogOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_catalog_item_endpoint(
    project_id: UUID,
    payload: EquipmentCatalogCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> EquipmentCatalogOut:
    try:
        item = await create_catalog_item(session, project_id=project_id, payload=payload)
    except DuplicateCatalogItemError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DUPLICATE_CATALOG_ITEM_DETAIL,
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="equipment_catalog.create",
        entity_type="equipment_catalog",
        entity_id=str(item.id),
        changes={"item_code": item.item_code, "category_batch": item.category_batch},
    )
    output = EquipmentCatalogOut.model_validate(item)
    await session.commit()
    return output


async def _load_item_or_404(
    session: AsyncSession,
    project_id: UUID,
    equipment_id: UUID,
) -> EquipmentCatalog:
    item = await get_catalog_item(session, project_id, equipment_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CATALOG_ITEM_NOT_FOUND_DETAIL,
        )
    return item


@router.post(
    "/catalog/{equipment_id}/sample-inspections",
    response_model=SampleInspectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_sample_inspection_endpoint(
    project_id: UUID,
    equipment_id: UUID,
    payload: SampleInspectionCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> SampleInspectionOut:
    item = await _load_item_or_404(session, project_id, equipment_id)
    try:
        inspection = await create_sample_inspection(session, item=item, payload=payload)
    except SampleInspectionError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="sample_inspection.create",
        entity_type="sample_inspection",
        entity_id=str(inspection.id),
        changes={"equipment_id": str(equipment_id), "conclusion": inspection.conclusion},
    )
    output = SampleInspectionOut.model_validate(inspection)
    await session.commit()
    return output


@router.get(
    "/catalog/{equipment_id}/sample-inspections",
    response_model=list[SampleInspectionOut],
)
async def list_sample_inspections_endpoint(
    project_id: UUID,
    equipment_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[SampleInspection]:
    await _load_item_or_404(session, project_id, equipment_id)
    return await list_sample_inspections(session, equipment_id)
