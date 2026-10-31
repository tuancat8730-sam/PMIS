from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beneficiary_unit import BeneficiaryUnit, UnitType

FORMER_NAME_SUFFIX = " cũ"


class DuplicateUnitError(Exception):
    """Mã đơn vị đã tồn tại trong dự án."""


def display_dual_name(official_name: str, former_name: str | None) -> str:
    """Tên hiển thị sau sáp nhập: "Tên mới (Tên cũ cũ)", hoặc chỉ tên mới nếu không có tên cũ."""
    cleaned_former = (former_name or "").strip()
    if not cleaned_former:
        return official_name
    return f"{official_name} ({cleaned_former}{FORMER_NAME_SUFFIX})"


async def create_unit(
    session: AsyncSession,
    *,
    project_id: UUID,
    values: Mapping[str, Any],
) -> BeneficiaryUnit:
    unit = BeneficiaryUnit(project_id=project_id, **values)
    session.add(unit)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateUnitError(str(values["unit_code"])) from exc
    return unit


async def list_units(
    session: AsyncSession,
    project_id: UUID,
    *,
    cluster_code: str | None = None,
    unit_type: UnitType | None = None,
) -> list[BeneficiaryUnit]:
    query = select(BeneficiaryUnit).where(BeneficiaryUnit.project_id == project_id)
    if cluster_code is not None:
        query = query.where(BeneficiaryUnit.cluster_code == cluster_code)
    if unit_type is not None:
        query = query.where(BeneficiaryUnit.unit_type == unit_type)
    result = await session.execute(query.order_by(BeneficiaryUnit.unit_code))
    return list(result.scalars().all())


async def find_unit_by_code(
    session: AsyncSession, project_id: UUID, unit_code: str
) -> BeneficiaryUnit | None:
    result = await session.execute(
        select(BeneficiaryUnit).where(
            BeneficiaryUnit.project_id == project_id,
            BeneficiaryUnit.unit_code == unit_code,
        )
    )
    return result.scalar_one_or_none()


async def get_unit(
    session: AsyncSession, project_id: UUID, unit_id: UUID
) -> BeneficiaryUnit | None:
    result = await session.execute(
        select(BeneficiaryUnit).where(
            BeneficiaryUnit.id == unit_id,
            BeneficiaryUnit.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


def apply_update(unit: BeneficiaryUnit, changes: Mapping[str, Any]) -> dict[str, Any]:
    """Gán các trường đã gửi lên và trả về phần thay đổi để ghi audit."""
    for field_name, value in changes.items():
        setattr(unit, field_name, value)
    return dict(changes)
