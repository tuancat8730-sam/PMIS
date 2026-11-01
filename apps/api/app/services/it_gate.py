"""Cổng nghiệm thu CNTT: ghép dữ liệu DB (ATTT, pentest, NFR) rồi gọi quy tắc thuần cho mốc M8."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.it_gate_rules import it_completion_blockers
from app.core.it_statuses import BLOCKING_SEVERITIES, UNRESOLVED_FIX_STATUSES
from app.core.nfr_rules import NfrCriterion, NfrResult, criteria_from_json, evaluate_nfr
from app.models.legal_document import DocMaturityStatus, LegalDocument
from app.models.pentest_finding import PentestFinding
from app.services.it_system import latest_nfr_measurements, list_modules

# Hồ sơ ATTT cấp độ 3 được nhận diện theo tên văn bản; cần xác nhận với danh sách pháp lý thật.
ATTT_DOSSIER_NAME_PATTERN = "%an toàn thông tin%"


async def attt_dossier_closed(session: AsyncSession, project_id: UUID) -> bool:
    """Đã khóa khi có ít nhất một hồ sơ ATTT và mọi hồ sơ ATTT đều ở VERIFIED_CLOSED."""
    result = await session.execute(
        select(LegalDocument.maturity_status).where(
            LegalDocument.project_id == project_id,
            LegalDocument.doc_name.ilike(ATTT_DOSSIER_NAME_PATTERN),
        )
    )
    statuses = list(result.scalars().all())
    return bool(statuses) and all(
        status == DocMaturityStatus.VERIFIED_CLOSED for status in statuses
    )


async def open_blocking_pentest_count(session: AsyncSession, project_id: UUID) -> int:
    """Số lỗi Critical/High còn mở (chưa FIXED/VERIFIED)."""
    result = await session.execute(
        select(func.count(PentestFinding.id)).where(
            PentestFinding.project_id == project_id,
            PentestFinding.severity.in_(BLOCKING_SEVERITIES),
            PentestFinding.fix_status.in_(UNRESOLVED_FIX_STATUSES),
        )
    )
    return int(result.scalar_one())


async def project_nfr_criteria(session: AsyncSession, project_id: UUID) -> tuple[NfrCriterion, ...]:
    """Gộp ngưỡng NFR từ `nfr_metrics` của mọi phân hệ; không có phân hệ thì không có chỉ tiêu."""
    merged: dict[str, dict[str, str]] = {}
    for module in await list_modules(session, project_id):
        merged.update(module.nfr_metrics or {})
    return criteria_from_json(merged)


async def project_nfr_results(session: AsyncSession, project_id: UUID) -> tuple[NfrResult, ...]:
    criteria = await project_nfr_criteria(session, project_id)
    measurements = await latest_nfr_measurements(session, project_id)
    return evaluate_nfr(criteria, measurements)


async def it_completion_blockers_for_project(
    session: AsyncSession, project_id: UUID
) -> tuple[str, ...]:
    """Lý do chặn hoàn thành mốc M8 của dự án CNTT. Rỗng nghĩa là được phép."""
    return it_completion_blockers(
        await attt_dossier_closed(session, project_id),
        await open_blocking_pentest_count(session, project_id),
        await project_nfr_results(session, project_id),
    )
