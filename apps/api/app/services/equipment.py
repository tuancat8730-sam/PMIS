from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sample_criteria import (
    CriterionResult,
    approval_status_for,
    ensure_codes_match_catalog,
    evaluate_sample,
)
from app.core.sample_criteria_catalog import SAMPLE_CRITERIA
from app.models.equipment import EquipmentCatalog, SampleInspection
from app.schemas.equipment import EquipmentCatalogCreate, SampleInspectionCreate


class DuplicateCatalogItemError(Exception):
    """Mã hàng đã có trong cùng dự án và đợt (G1)."""


async def list_catalog(session: AsyncSession, project_id: UUID) -> list[EquipmentCatalog]:
    result = await session.execute(
        select(EquipmentCatalog)
        .where(EquipmentCatalog.project_id == project_id)
        .order_by(EquipmentCatalog.category_batch, EquipmentCatalog.item_code)
    )
    return list(result.scalars().all())


async def get_catalog_item(
    session: AsyncSession,
    project_id: UUID,
    equipment_id: UUID,
) -> EquipmentCatalog | None:
    result = await session.execute(
        select(EquipmentCatalog).where(
            EquipmentCatalog.id == equipment_id,
            EquipmentCatalog.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def create_catalog_item(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: EquipmentCatalogCreate,
) -> EquipmentCatalog:
    item = EquipmentCatalog(project_id=project_id, **payload.model_dump())
    session.add(item)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateCatalogItemError(payload.item_code) from exc
    return item


async def create_sample_inspection(
    session: AsyncSession,
    *,
    item: EquipmentCatalog,
    payload: SampleInspectionCreate,
) -> SampleInspection:
    """Kiểm định mẫu, cập nhật trạng thái phê duyệt của mã hàng theo kết luận."""
    criteria = [CriterionResult(code=c.code, result=c.result) for c in payload.criteria]
    catalog_codes = [criterion.code for criterion in SAMPLE_CRITERIA]
    verdict = evaluate_sample(criteria, expected_count=len(catalog_codes))
    ensure_codes_match_catalog([criterion.code for criterion in criteria], catalog_codes)

    inspection = SampleInspection(
        equipment_id=item.id,
        inspected_on=payload.inspected_on,
        inspector=payload.inspector,
        serial_number_sample=payload.serial_number_sample,
        criteria_results=[{"code": c.code, "result": c.result} for c in criteria],
        conclusion=verdict.conclusion,
    )
    session.add(inspection)
    item.sample_approval_status = approval_status_for(verdict.conclusion)
    if payload.serial_number_sample is not None:
        item.sample_serial_number = payload.serial_number_sample
    await session.flush()
    return inspection


async def list_sample_inspections(
    session: AsyncSession,
    equipment_id: UUID,
) -> list[SampleInspection]:
    result = await session.execute(
        select(SampleInspection)
        .where(SampleInspection.equipment_id == equipment_id)
        .order_by(SampleInspection.inspected_on.desc())
    )
    return list(result.scalars().all())
