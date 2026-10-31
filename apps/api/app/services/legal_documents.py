from collections.abc import Iterable, Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.legal_maturity_rules import can_transition, is_locked, requires_reason
from app.models.legal_document import DocMaturityStatus, LegalDocument, LegalPhaseGroup
from app.schemas.legal_documents import LegalDocumentSummary


class DuplicateSttError(Exception):
    """Số thứ tự (`stt`) đã tồn tại trong dự án."""


class StatusConflictError(Exception):
    """Trạng thái gửi lên không khớp trạng thái hiện tại, hoặc chuyển trạng thái không hợp lệ."""


class ReasonRequiredError(Exception):
    """Chuyển trạng thái này bắt buộc có lý do."""


class LockedDocumentError(Exception):
    """Hồ sơ đã đóng (VERIFIED_CLOSED) không sửa trực tiếp được."""


async def get_legal_document(
    session: AsyncSession,
    project_id: UUID,
    document_id: UUID,
) -> LegalDocument | None:
    result = await session.execute(
        select(LegalDocument).where(
            LegalDocument.id == document_id,
            LegalDocument.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def list_legal_documents(
    session: AsyncSession,
    project_id: UUID,
    phase_group: LegalPhaseGroup | None,
    maturity_status: DocMaturityStatus | None,
) -> list[LegalDocument]:
    query = select(LegalDocument).where(LegalDocument.project_id == project_id)
    if phase_group is not None:
        query = query.where(LegalDocument.phase_group == phase_group)
    if maturity_status is not None:
        query = query.where(LegalDocument.maturity_status == maturity_status)
    result = await session.execute(query.order_by(LegalDocument.stt))
    return list(result.scalars().all())


async def create_legal_document(
    session: AsyncSession,
    *,
    project_id: UUID,
    values: Mapping[str, Any],
) -> LegalDocument:
    document = LegalDocument(project_id=project_id, **values)
    session.add(document)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateSttError(values["stt"]) from exc
    return document


def update_legal_document(document: LegalDocument, changes: Mapping[str, Any]) -> None:
    """Gán các trường đã sửa lên bản ghi. Từ chối nếu hồ sơ đã khóa."""
    if is_locked(document.maturity_status):
        raise LockedDocumentError(str(document.id))
    for field, value in changes.items():
        setattr(document, field, value)


def transition_legal_document(
    document: LegalDocument,
    *,
    expected_status: DocMaturityStatus,
    target_status: DocMaturityStatus,
    reason: str | None,
) -> DocMaturityStatus:
    """Đổi trạng thái sau khi kiểm tra; trả về trạng thái cũ để router ghi audit."""
    current = document.maturity_status
    if current != expected_status:
        raise StatusConflictError(
            f"Trạng thái hiện tại là {current.value}, không phải {expected_status.value}"
        )
    if not can_transition(current, target_status):
        raise StatusConflictError(f"Không thể chuyển từ {current.value} sang {target_status.value}")
    if requires_reason(current, target_status) and not (reason and reason.strip()):
        raise ReasonRequiredError(target_status.value)
    document.maturity_status = target_status
    return current


async def count_by_phase_and_status(
    session: AsyncSession,
    project_id: UUID,
) -> list[tuple[LegalPhaseGroup, DocMaturityStatus, int]]:
    result = await session.execute(
        select(
            LegalDocument.phase_group,
            LegalDocument.maturity_status,
            func.count(LegalDocument.id),
        )
        .where(LegalDocument.project_id == project_id)
        .group_by(LegalDocument.phase_group, LegalDocument.maturity_status)
    )
    return [(phase, status, int(count)) for phase, status, count in result.all()]


def build_summary(
    rows: Iterable[tuple[LegalPhaseGroup, DocMaturityStatus, int]],
) -> LegalDocumentSummary:
    """Gộp số đếm thành ma trận đủ mọi giai đoạn và trạng thái, ô không có hồ sơ là 0."""
    by_status = dict.fromkeys(DocMaturityStatus, 0)
    by_phase_group = {phase: dict.fromkeys(DocMaturityStatus, 0) for phase in LegalPhaseGroup}
    total = 0
    for phase, status, count in rows:
        by_status[status] += count
        by_phase_group[phase][status] += count
        total += count
    return LegalDocumentSummary(total=total, by_status=by_status, by_phase_group=by_phase_group)
