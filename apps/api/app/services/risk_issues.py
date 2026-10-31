from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.record_codes import build_record_code, next_sequence, record_prefix
from app.models.risk_issue import RecordType, RiskIssue


class DuplicateRecordCodeError(Exception):
    """Mã bản ghi vừa sinh đã bị một yêu cầu khác lấy trước (tranh chấp đồng thời)."""


async def get_risk_issue(
    session: AsyncSession,
    project_id: UUID,
    risk_issue_id: UUID,
) -> RiskIssue | None:
    result = await session.execute(
        select(RiskIssue).where(
            RiskIssue.id == risk_issue_id,
            RiskIssue.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def list_risk_issues(
    session: AsyncSession,
    project_id: UUID,
    record_type: RecordType | None,
) -> list[RiskIssue]:
    query = select(RiskIssue).where(RiskIssue.project_id == project_id)
    if record_type is not None:
        query = query.where(RiskIssue.record_type == record_type)
    result = await session.execute(query.order_by(RiskIssue.code))
    return list(result.scalars().all())


async def create_risk_issue(
    session: AsyncSession,
    *,
    project_id: UUID,
    project_code: str,
    values: Mapping[str, Any],
) -> RiskIssue:
    record_type = RecordType(values["record_type"])
    prefix = record_prefix(project_code, record_type)
    existing = await session.execute(
        select(RiskIssue.code).where(
            RiskIssue.project_id == project_id,
            RiskIssue.code.startswith(prefix),
        )
    )
    sequence = next_sequence(existing.scalars().all(), prefix)
    record = RiskIssue(
        project_id=project_id,
        code=build_record_code(project_code, record_type, sequence),
        **values,
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateRecordCodeError(record.code) from exc
    return record
