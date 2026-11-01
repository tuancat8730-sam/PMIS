from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.delivery_matrix import build_handover_slots, change_delivery_status
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.delivery_handover import DeliveryHandover

HandoverWithCluster = tuple[DeliveryHandover, str]


async def generate_handovers(session: AsyncSession, *, project_id: UUID) -> int:
    """Sinh dòng ma trận còn thiếu cho mọi đơn vị của dự án. Chạy lại không tạo bản trùng."""
    units_result = await session.execute(
        select(BeneficiaryUnit.id).where(BeneficiaryUnit.project_id == project_id)
    )
    unit_ids = [str(unit_id) for unit_id in units_result.scalars().all()]
    slots = build_handover_slots(unit_ids)

    existing_result = await session.execute(
        select(DeliveryHandover.beneficiary_unit_id, DeliveryHandover.batch_code).where(
            DeliveryHandover.project_id == project_id
        )
    )
    existing = {(str(unit_id), batch_code) for unit_id, batch_code in existing_result.all()}

    missing = [slot for slot in slots if (slot.unit_id, slot.batch_code) not in existing]
    for slot in missing:
        session.add(
            DeliveryHandover(
                project_id=project_id,
                beneficiary_unit_id=UUID(slot.unit_id),
                batch_code=slot.batch_code,
            )
        )
    await session.flush()
    return len(missing)


async def list_handovers(
    session: AsyncSession,
    *,
    project_id: UUID,
    cluster_code: str | None = None,
    batch_code: str | None = None,
) -> list[HandoverWithCluster]:
    query = (
        select(DeliveryHandover, BeneficiaryUnit.cluster_code)
        .join(BeneficiaryUnit, DeliveryHandover.beneficiary_unit_id == BeneficiaryUnit.id)
        .where(DeliveryHandover.project_id == project_id)
    )
    if cluster_code is not None:
        query = query.where(BeneficiaryUnit.cluster_code == cluster_code)
    if batch_code is not None:
        query = query.where(DeliveryHandover.batch_code == batch_code)
    query = query.order_by(BeneficiaryUnit.cluster_code, DeliveryHandover.batch_code)
    result = await session.execute(query)
    return [(handover, cluster) for handover, cluster in result.all()]


async def get_handover(
    session: AsyncSession,
    *,
    project_id: UUID,
    handover_id: UUID,
) -> HandoverWithCluster | None:
    result = await session.execute(
        select(DeliveryHandover, BeneficiaryUnit.cluster_code)
        .join(BeneficiaryUnit, DeliveryHandover.beneficiary_unit_id == BeneficiaryUnit.id)
        .where(
            DeliveryHandover.id == handover_id,
            DeliveryHandover.project_id == project_id,
        )
    )
    row = result.one_or_none()
    return None if row is None else (row[0], row[1])


def update_handover_status(handover: DeliveryHandover, target: str) -> DeliveryHandover:
    """Đổi trạng thái theo bảng chuyển trong `delivery_matrix`; ném lỗi nếu không được phép."""
    handover.delivery_status = change_delivery_status(handover.delivery_status, target)
    return handover
