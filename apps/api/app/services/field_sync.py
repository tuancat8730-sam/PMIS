from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_handover import DeliveryHandover
from app.models.equipment_serial import EquipmentSerial
from app.models.idempotency_key import IdempotencyKey


@dataclass(frozen=True)
class FieldWriteHeaders:
    """Hai header bắt buộc của lệnh ghi từ thiết bị hiện trường (CLAUDE.md, quy ước thiết bị)."""

    device_id: str
    idempotency_key: UUID


@dataclass(frozen=True)
class FieldWriteRequest:
    headers: FieldWriteHeaders
    endpoint: str
    request_hash: str


class IdempotencyKeyReusedError(Exception):
    """Cùng Idempotency-Key nhưng khác endpoint hoặc khác nội dung yêu cầu."""


class VersionConflictError(Exception):
    """Phiên bản thiết bị gửi lên đã cũ: bản ghi đã bị thiết bị khác sửa trước."""

    def __init__(self, current: dict[str, Any]) -> None:
        super().__init__("version conflict")
        self.current = current


async def find_recorded_response(
    session: AsyncSession,
    request: FieldWriteRequest,
) -> IdempotencyKey | None:
    """Trả kết quả đã ghi cho cùng khóa; ném lỗi nếu khóa đã dùng cho yêu cầu khác."""
    result = await session.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.device_id == request.headers.device_id,
            IdempotencyKey.idempotency_key == request.headers.idempotency_key,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    if row.endpoint != request.endpoint or row.request_hash != request.request_hash:
        raise IdempotencyKeyReusedError
    return row


def record_response(
    session: AsyncSession,
    request: FieldWriteRequest,
    *,
    status_code: int,
    body: dict[str, Any],
) -> None:
    """Ghi kết quả thành công vào session. Caller commit cùng thao tác nghiệp vụ."""
    session.add(
        IdempotencyKey(
            device_id=request.headers.device_id,
            idempotency_key=request.headers.idempotency_key,
            endpoint=request.endpoint,
            request_hash=request.request_hash,
            status_code=status_code,
            response_body=body,
        )
    )


def ensure_expected_version(
    row_version: int,
    expected_version: int,
    current: dict[str, Any],
) -> None:
    if row_version != expected_version:
        raise VersionConflictError(current)


async def lock_handover(
    session: AsyncSession,
    *,
    project_id: UUID,
    handover_id: UUID,
) -> DeliveryHandover | None:
    """Khóa dòng giao hàng cho tới khi commit, tránh hai thiết bị ghi chồng nhau."""
    result = await session.execute(
        select(DeliveryHandover)
        .where(DeliveryHandover.id == handover_id, DeliveryHandover.project_id == project_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def lock_serial(
    session: AsyncSession,
    *,
    project_id: UUID,
    serial_id: UUID,
) -> EquipmentSerial | None:
    result = await session.execute(
        select(EquipmentSerial)
        .where(EquipmentSerial.id == serial_id, EquipmentSerial.project_id == project_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()
